import re

from redis import StrictRedis
from archives.lib.connections import redis_pool

redis = StrictRedis(connection_pool=redis_pool)
blogs = set()

with open("tumblr_posts.txt", "r") as f:
    for line in f:
        match = re.search(r"://([\w\d]+\.tumblr.com)", line)
        if not match:
            continue

        blogs.add(match.group(1))

for blog in blogs:
    redis.sadd("tumblr:urls", blog)
    # print(blog)