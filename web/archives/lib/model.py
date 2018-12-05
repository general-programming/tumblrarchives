# This Python file uses the following encoding: utf-8
import os

from bs4 import BeautifulSoup
from sqlalchemy import Column, Integer, String, create_engine, inspect
from sqlalchemy.dialects.postgresql import JSONB
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

class Post(Base):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True)
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

    data = Column(JSONB, nullable=False)
    extra_meta = Column(JSONB)

# Index for querying by url.
Index("index_post_url", Post.url)
