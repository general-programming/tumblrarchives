# This Python file uses the following encoding: utf-8
from archives.lib.model import sm, Post
from sqlalchemy import func
from flask import g

def connect_sql():
    g.sql = sm()

def before_request():
    g.rowcount = g.sql.query(func.count(Post.id)).scalar()
    g.blogcount = g.sql.query(func.count(func.distinct(Post.url))).scalar()

def disconnect_sql(result=None):
    g.sql.close()
    del g.sql
    return result
