# This Python file uses the following encoding: utf-8
import os

from archives.lib.model import sm, Post
from sqlalchemy import func
from flask import g, request, current_app

def connect_sql():
    g.sql = sm()

def before_request():
    g.rowcount = g.sql.query(func.count(Post.id)).scalar()
    g.blogcount = g.sql.query(func.count(func.distinct(Post.url))).scalar()

def disconnect_sql(result=None):
    if hasattr(g, "sql"):
        g.sql.close()
        del g.sql

    return result

file_hashes = {}

def cache_breaker(endpoint, values):
    if 'static' == endpoint or endpoint.endswith('.static'):
        filename = values.get('filename')
        if filename:
            if '.' in endpoint:
                blueprint = endpoint.rsplit('.', 1)[0]
            else:
                blueprint = request.blueprint

            if blueprint:
                static_folder = current_app.blueprints[blueprint].static_folder or current_app.static_folder
            else:
                static_folder = current_app.static_folder

            values['q'] = static_file_hash(os.path.join(static_folder, filename))

def static_file_hash(filename):
    if filename not in file_hashes:
        file_hashes[filename] = int(os.stat(filename).st_mtime)

    return file_hashes[filename]
