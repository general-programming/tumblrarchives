# This Python file uses the following encoding: utf-8
import os
import uuid
import pytumblr

from archives.lib.model import sm
from flask import abort, current_app, g, request
from redis import ConnectionPool, StrictRedis

redis_pool = ConnectionPool(
    host=os.environ.get('REDIS_PORT_6379_TCP_ADDR', os.environ.get('REDIS_HOST', '127.0.0.1')),
    port=int(os.environ.get('REDIS_PORT_6379_TCP_PORT', os.environ.get('REDIS_PORT', 6379))),
    db=int(os.environ.get('REDIS_DB', 0)),
    decode_responses=True
)

def set_cookie(response):
    if "archives" not in request.cookies and hasattr(g, "session_id"):
        response.set_cookie(
            "archives",
            g.session_id,
            max_age=365 * 24 * 60 * 60,
            httponly=True,
        )
    return response


def check_csrf_token():
    if request.endpoint == "static":
        return

    # Check CSRF only for POST requests.
    if request.method != "POST":
        return

    # Ignore CSRF only for local debugging.
    if 'NOCSRF' in os.environ:
        return

    token = g.redis.hget("session:%s" % g.session_id, "csrf")
    if "token" in request.form and request.form["token"] == token:
        return
    abort(403)

def connect_sql():
    if request.endpoint == "static":
        return

    g.sql = sm()

def connect_redis():
    if request.endpoint == "static":
        return

    g.redis = StrictRedis(connection_pool=redis_pool)

    if "archives" in request.cookies:
        g.session_id = request.cookies["archives"]
        g.user_data = g.redis.hgetall("session:" + g.session_id)
        if g.user_data is not None:
            g.user_data = {}
    else:
        g.session_id = str(uuid.uuid4())
        g.user_id = None

    g.csrf_token = g.redis.hget("session:%s" % g.session_id, "csrf")
    if g.csrf_token is None:
        g.csrf_token = str(uuid.uuid4())
        g.redis.hset("session:%s" % g.session_id, "csrf", g.csrf_token)
        g.redis.expire("session:%s" % g.session_id, 3600)

def before_request():
    if request.endpoint == "static":
        return

    g.tumblr = pytumblr.TumblrRestClient(
        os.environ.get("TUMBLR_CONSUMER_KEY"),
        os.environ.get("TUMBLR_CONSUMER_SECRET")
    )

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
