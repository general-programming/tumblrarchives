import random
import time

from redis import StrictRedis
from archives.lib.connections import redis_pool, create_tumblr
from archives.lib.model import Post, Blog, sm


sql = sm()
redis = StrictRedis(connection_pool=redis_pool)
tumblr = create_tumblr()

remain = redis.scard("tumblr:urls") - redis.scard("tumblr:done")

urls = list(redis.smembers("tumblr:blogs2"))
backoff = 2

while len(urls) > 0:
    url = urls.pop(random.randrange(len(urls)))

    # Skip over blogs we've already passed through.
    if redis.sismember("tumblr:done", url):
        continue

    # press f for performance
    if sql.query(Blog).filter(Blog.url == url).scalar():
        redis.sadd("tumblr:done", url)
        continue

    # Query
    info = tumblr.blog_info(url)
    remain -= 1

    # Ignore 404s
    if "meta" in info:
        if info["meta"]["status"] == 404:
            print(f"{url} - 404")
            redis.sadd("tumblr:done", url)
            redis.sadd("tumblr:404", url)
            continue
        elif info["meta"]["status"] == 429:
            urls.append(url)
            print(f"Got 429. Backing off for {backoff} secs.")
            time.sleep(backoff)
            backoff = min(120, backoff ** random.uniform(1, 2))
            continue

    # wot how
    if "blog" not in info:
        print(info)
        print()
        redis.sadd("tumblr:done", url)
        redis.sadd("tumblr:badinfo", url)
        continue

    # Reset backoff if we make it this far.
    if backoff != 2:
        backoff = 2

    # Make a new blog
    new_blog = Blog.create_from_metadata(sql, info)
    sql.commit()

    # Log the goodness
    print(f"{url} - {info['blog']['posts']} posts; {remain} remaining.")
    redis.sadd("tumblr:done", url)