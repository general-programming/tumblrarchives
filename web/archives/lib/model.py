# This Python file uses the following encoding: utf-8
import os

from urllib.parse import urlparse
from contextlib import contextmanager

from bs4 import BeautifulSoup

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, create_engine, inspect
from sqlalchemy.dialects.postgresql import JSONB, insert
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
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
    author = Column(ForeignKey("blogs.id"))
    url = Column(String(200))
    data = Column(JSONB, nullable=False)

    def get_linked_blogs(self):
        TEXT_KEYS = ["caption", "body", "content", "tree_html"]
        sql = inspect(self).session

        links = set()
        blogs = set()

        # Find links
        for post in sql.query(Post).filter(Post.url == self.url):
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

class Blog(Base):
    __tablename__ = "blogs"
    id = Column(Integer, primary_key=True)
    tumblr_uid = Column(String, nullable=False)
    url = Column(String(200))
    name = Column(String(200))

    nsfw = Column(Boolean, server_default='f')
    total_posts = Column(Integer, server_default='0', nullable=False)

    data = Column(JSONB, nullable=False)
    extra_meta = Column(JSONB)

    @classmethod
    def create_from_metadata(cls, db, info):
        # Try to work with an existing blog object first.
        blog_object = db.query(Blog).filter(Blog.tumblr_uid == info["blog"]["uuid"]).scalar()

        # Setup the new data to update.
        blog_data = dict(
            url=urlparse(info["blog"].pop("url")).netloc,
            name=info["blog"].pop("name"),
            nsfw=info["blog"].pop("is_nsfw", False),
            extra_meta=info.get("meta", {})
        )

        # Make sure we do not bump total posts down.
        blog_data["total_posts"] = max(
            info["blog"].pop("total_posts"),
            getattr(blog_object, "total_posts", 0)
        )

        # The UUID never changes.
        if not blog_object:
            blog_data["tumblr_uid"] = info["blog"].pop("uuid"),

        # Insert what's left of the data into the data
        blog_data["data"] = info["blog"]

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
Index("index_post_url", Post.url)
Index("blog_uid_unique", Blog.tumblr_uid, unique=True)
