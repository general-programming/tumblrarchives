import os

import pytumblr
from redis import ConnectionPool

redis_pool = ConnectionPool(
    host=os.environ.get('REDIS_PORT_6379_TCP_ADDR', os.environ.get('REDIS_HOST', '127.0.0.1')),
    port=int(os.environ.get('REDIS_PORT_6379_TCP_PORT', os.environ.get('REDIS_PORT', 6379))),
    db=int(os.environ.get('REDIS_DB', 0)),
    decode_responses=True
)

def create_tumblr():
    return pytumblr.TumblrRestClient(
        os.environ.get("TUMBLR_CONSUMER_KEY"),
        os.environ.get("TUMBLR_CONSUMER_SECRET")
    )
