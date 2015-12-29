# This Python file uses the following encoding: utf-8
import os

from flask import g, request, current_app
from redis import StrictRedis, ConnectionPool
from sqlalchemy import func

from archives.lib.model import sm, Post

redis_pool = ConnectionPool(
    host=os.environ.get('REDIS_PORT_6379_TCP_ADDR', os.environ.get('REDIS_HOST', '127.0.0.1')),
    port=int(os.environ.get('REDIS_PORT_6379_TCP_PORT', os.environ.get('REDIS_PORT', 6379))),
    db=int(os.environ.get('REDIS_DB', 0)),
    decode_responses=True
)

def connect_sql():
    g.sql = sm()

def connect_redis():
    g.redis = StrictRedis(connection_pool=redis_pool)

def before_request():
    g.rowcount = g.sql.query(func.count(Post.id)).scalar()

def disconnect_sql(result=None):
    if hasattr(g, "sql"):
        g.sql.close()
        del g.sql

    return result

def disconnect_redis(result=None):
    if hasattr(g, "redis"):
        del g.redis

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
