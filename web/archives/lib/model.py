# This Python file uses the following encoding: utf-8
import os
import datetime

from urllib.parse import urlparse
from contextlib import contextmanager

from bs4 import BeautifulSoup

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, BigInteger, DateTime, Unicode, create_engine, inspect
from sqlalchemy.dialects.postgresql import JSONB, ARRAY, insert
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from sqlalchemy.schema import Index

from archives.lib.utils import clean_data

debug = os.environ.get('DEBUG', False)

engine = create_engine(os.environ["POSTGRES_URL"], convert_unicode=True, pool_recycle=3600)

if debug:
    engine.echo = True

sm = sessionmaker(autocommit=False,
                  autoflush=False,
                  bind=engine)

base_session = scoped_session(sm)

Base = declarative_base()
Base.query = base_session.query_property()

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = sm()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


class Post(Base):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True)
    author_id = Column(ForeignKey("blogs.id"))
    tumblr_id = Column(BigInteger)

    posted = Column(DateTime)

    post_type = Column(String)
    tags = Column(ARRAY(Unicode))
    format = Column(String)
    state = Column(String)

    note_count = Column(Integer)
    reblog_key = Column(String)

    url = Column(String(200))
    slug = Column(Unicode)
    summary = Column(Unicode)

    author = relationship("Blog")
    # photos = relationship("Photo")

    body = Column(Unicode)
    data = Column(JSONB, nullable=False)

    def to_dict(self, with_meta=True):
        result = dict(
            posted=self.posted.strftime("%Y-%m-%d %H:%M:%S %Z"),
            post_type=self.post_type,
            tags=self.tags,
            format=self.format,
            state=self.state,
            note_count=self.note_count,
            reblog_key=self.reblog_key,
            slug=self.slug,
            summary=self.summary
        )

        result.update(self.data)
        
        if with_meta:
            with session_scope() as db:
                meta = db.query(PostMeta).filter(PostMeta.id == self.id).scalar()
                result["meta"] = meta.to_dict()

        return result

    @classmethod
    def create_from_metadata(cls, db, info):
        # Try to work with an existing blog object first.
        post_object = db.query(Post).filter(Post.tumblr_id == info["id"]).scalar()

        # Setup the new data to update.
        post_data = dict(
            tumblr_id=info.pop("id"),
        )

        # Post body
        if "body" in info and info["body"]:
            post_data["body"] = info.pop("body")

        # Post time
        info.pop("date", None)
        if not post_object or not post_object.posted:
            post_epoch = info.pop("timestamp", 0)
            post_data["posted"] = max(
                datetime.datetime.fromtimestamp(post_epoch),
                getattr(post_object, "posted", datetime.datetime.fromtimestamp(post_epoch))
            )
        else:
            info.pop("timestamp", None)

        # Update the note count.
        post_data["note_count"] = max(
            info.pop("note_count", 0),
            getattr(post_object, "note_count", 0)
        )

        # Other args
        post_data["post_type"] = info.pop("type", getattr(post_object, "format", None))
        post_data["format"] = info.pop("format", getattr(post_object, "format", None))
        post_data["reblog_key"] = info.pop("reblog_key", getattr(post_object, "reblog_key", None))
        post_data["tags"] = info.pop("tags", getattr(post_object, "tags", []))

        post_data["slug"] = info.pop("slug", getattr(post_object, "slug", ""))
        post_data["state"] = info.pop("state", getattr(post_object, "state", "published"))
        post_data["summary"] = info.pop("summary", getattr(post_object, "summary", ""))

        # Update/add blog entries
        author = []

        if "blog" in info:
            updated_blog_data = info["blog"]
            if "uuid" not in updated_blog_data:
                info["blog"].pop()
            else:
                author.append(Blog.create_from_metadata(db, info.pop("blog")))
                db.flush()

        # Set the author id if it is not set
        if not post_object or not post_object.author_id:
            blog_name = info.pop("blog_name", "")
            if not author:
                author = db.query(Blog).filter(Blog.name == blog_name).order_by(Blog.total_posts.desc()).all()
            try:
                post_data["author_id"] = author[0].id
            except IndexError:
                pass
        else:
            info.pop("blog_name", "")

        # Pop away user specific fields.
        for key in ["followed", "liked"]:
            info.pop(key, None)

        # Pop away fields that would be empty.
        for key in ["trail", "recommended_color", "recommended_source"]:
            if not info.get(key, None):
                info.pop(key, None)

        # Insert what's left of the data into the data
        post_data["data"] = info

        # Clean the data of null bytes.
        clean_data(post_data)

        # Create / Update the post object.
        if not post_object:
            # Insert and query the blog object if it does not exist.
            db.execute(insert(Post).values(
                **post_data
            ).on_conflict_do_update(index_elements=["tumblr_id", "author_id"], set_=post_data))
            post_object = db.query(Post).filter(
                Post.tumblr_id == post_data["tumblr_id"]
            ).scalar()
        else:
            for key, value in post_data.items():
                setattr(post_object, key, value)

        # Create / Update a post metadata object.
        data_copy = post_object.data.copy()
        post_meta = PostMeta.create_from_metadata(db, data_copy, post_object.id)
        post_object.data = data_copy

        db.flush()

        return post_object

    def get_linked_blogs(self):
        TEXT_KEYS = ["caption", "body", "content", "tree_html"]
        sql = inspect(self).session

        links = set()
        blogs = set()

        # Find links
        for post in sql.query(Post).filter(Post.author_id == self.author_id):
            content = ""

            for key in TEXT_KEYS:
                content = content + post.data.get(key, "").strip()

            if not content:
                continue

            soup = BeautifulSoup(content, "html5lib")
            for link in soup.find_all("a"):
                try:
                    links.add(link["href"])
                except KeyError:
                    pass

        # Convert links to Tumblr URLs
        for link in links:
            if "tumblr.com" not in link:
                continue
            blogs.add(link.split(".")[0].lstrip("http://").lstrip("https://"))

        return blogs

class PostMeta(Base):
    __tablename__ = "posts_meta"

    id = Column(ForeignKey("posts.id"), primary_key=True)
    post = relationship("Post")

    can_like = Column(Boolean, server_default='t')
    can_reblog = Column(Boolean, server_default='t')
    can_reply = Column(Boolean, server_default='t')
    display_avatar = Column(Boolean, server_default='t')
    is_blocks_post_format = Column(Boolean, server_default='f')
    can_send_in_message = Column(Boolean, server_default='t')
    post_url = Column(String)
    short_url = Column(String)

    def to_dict(self):
        return dict(
            post_url=self.post_url,
            short_url=self.short_url,
            can_like=self.can_like,
            can_reblog=self.can_reblog,
            can_reply=self.can_reply,
            display_avatar=self.display_avatar,
            is_blocks_post_format=self.is_blocks_post_format,
            can_send_in_message=self.can_send_in_message
        )

    @classmethod
    def create_from_metadata(cls, db, info, post_id):
        # Try to work with an existing object first.
        meta_object = db.query(PostMeta).filter(PostMeta.id == post_id).scalar()

        # Setup the new data to update.
        meta_data = dict(
            id=post_id,
        )

        # Set from pops
        meta_data["can_like"] = info.pop("can_like", getattr(meta_object, "can_like", True))
        meta_data["can_reblog"] = info.pop("can_reblog", getattr(meta_object, "can_reblog", True))
        meta_data["can_reply"] = info.pop("can_reply", getattr(meta_object, "can_reply", True))
        meta_data["display_avatar"] = info.pop("display_avatar", getattr(meta_object, "display_avatar", True))
        meta_data["is_blocks_post_format"] = info.pop("is_blocks_post_format", getattr(meta_object, "is_blocks_post_format", False))
        meta_data["can_send_in_message"] = info.pop("can_send_in_message", getattr(meta_object, "can_send_in_message", True))

        meta_data["post_url"] = info.pop("post_url", getattr(meta_object, "post_url", ""))
        meta_data["short_url"] = info.pop("short_url", getattr(meta_object, "short_url", ""))

        # Create / Update the meta object.
        if not meta_object:
            # Insert and query the blog object if it does not exist.
            db.execute(insert(PostMeta).values(
                **meta_data
            ).on_conflict_do_update(index_elements=["id"], set_=meta_data))
            meta_object = db.query(PostMeta).filter(
                PostMeta.id == meta_data["id"]
            ).scalar()
        else:
            for key, value in meta_data.items():
                setattr(meta_object, key, value)

        return meta_object

class Blog(Base):
    __tablename__ = "blogs"
    id = Column(Integer, primary_key=True)
    tumblr_uid = Column(String, nullable=False)
    url = Column(String(200))
    name = Column(String(200))

    updated = Column(DateTime)
    last_crawl_update = Column(DateTime)

    nsfw = Column(Boolean, server_default='f')
    total_posts = Column(Integer, server_default='0', nullable=False)
    total_likes = Column(Integer, server_default='0', nullable=False)

    theme = Column(JSONB)
    data = Column(JSONB, nullable=False)
    extra_meta = Column(JSONB)

    @classmethod
    def create_from_metadata(cls, db, info):
        if "blog" in info:
            blog_info = info["blog"]
        else:
            blog_info = info

        # Try to work with an existing blog object first.
        blog_object = db.query(Blog).filter(Blog.tumblr_uid == blog_info["uuid"]).scalar()

        # Setup the new data to update.
        # info.pop("format", getattr(post_object, "format", None))
        blog_data = dict(
            url=urlparse(blog_info.pop("url")).netloc,
            name=blog_info.pop("name", getattr(blog_object, "name", None)),
            nsfw=blog_info.pop("is_nsfw", getattr(blog_object, "nsfw", False)),
            extra_meta=info.get("meta", {})
        )

        # Make sure we do not bump total posts down.
        blog_data["total_posts"] = max(
            blog_info.pop("total_posts", 0),
            getattr(blog_object, "total_posts", 0)
        )

        # Update the updated time.
        updated_epoch = blog_info.pop("updated", 0)
        blog_data["updated"] = max(
            datetime.datetime.fromtimestamp(updated_epoch),
            getattr(blog_object, "updated", datetime.datetime.fromtimestamp(updated_epoch))
        )

        # The UUID never changes.
        if not blog_object:
            blog_data["tumblr_uid"] = blog_info.pop("uuid")
        else:
            # Pop the UUID away from the blog object.
            blog_info.pop("uuid")

        # Theme
        if "theme" in blog_info:
            blog_data["theme"] = blog_info.pop("theme")

        # Insert what's left of the data into the data
        blog_data["data"] = blog_info

        # Clean the data of null bytes.
        clean_data(blog_data)

        if not blog_object:
            # Insert and query the blog object if it does not exist.
            db.execute(insert(Blog).values(
                **blog_data
            ).on_conflict_do_update(index_elements=["tumblr_uid"], set_=blog_data))
            blog_object = db.query(Blog).filter(
                Blog.tumblr_uid == blog_data["tumblr_uid"]
            ).scalar()
        else:
            for key, value in blog_data.items():
                setattr(blog_object, key, value)

        return blog_object

# Index for querying by url.
Index("index_blog_name", Blog.name)
Index("post_tumblr_id_unique", Post.tumblr_id, Post.author_id, unique=True)
Index("blog_uid_unique", Blog.tumblr_uid, unique=True)
