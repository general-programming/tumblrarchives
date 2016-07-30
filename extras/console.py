import code
from redis import StrictRedis
from archives.lib.connections import create_tumblr, redis_pool
from archives.tasks.tumblr import add_post, archive_post, archive_blog

redis = StrictRedis(connection_pool=redis_pool)
tumblr = create_tumblr()

if __name__ == "__main__":
    code.interact(local=dict(globals(), **locals()))
