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

    data = Column(JSONB, nullable=False)
    extra_meta = Column(JSONB)

    @classmethod
    def create_from_metadata(cls, db, info):
        blog_data = dict(
            url=urlparse(info["blog"].pop("url")).netloc,
            name=info["blog"].pop("name"),
            tumblr_uid=info["blog"].pop("uuid"),
            nsfw=info["blog"].pop("is_nsfw", False),
            extra_meta=info.get("meta", {})
        )
        blog_data["data"] = info["blog"]
    
        db.execute(insert(Blog).values(
            **blog_data
        ).on_conflict_do_update(index_elements=["tumblr_uid"], set_=blog_data))

        return db.query(Blog).filter(
            Blog.tumblr_uid == blog_data["tumblr_uid"]
        ).scalar()

# Index for querying by url.
Index("index_post_url", Post.url)
Index("blog_uid_unique", Blog.tumblr_uid, unique=True)
