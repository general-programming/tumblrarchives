# This Python file uses the following encoding: utf-8
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.schema import Index
from sqlalchemy.dialects.postgresql import JSONB

import os

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

# Index for querying by url.
Index("index_post_url", Post.url)
