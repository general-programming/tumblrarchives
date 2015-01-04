from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import JSONB

import os

engine = create_engine(os.environ["POSTGRES_URL"], convert_unicode=True, pool_recycle=3600)
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
