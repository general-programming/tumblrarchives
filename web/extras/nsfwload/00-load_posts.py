import re
import gzip
import sys

from redis import StrictRedis
from archives.lib.connections import redis_pool

redis = StrictRedis(connection_pool=redis_pool)
blogs = set()

with gzip.open("blogs1M.csv.gz", "r") as f:
    for line in f:
        line = line.decode("utf8")

        match = re.search(r"://([\w\d]+\.tumblr.com)", line)
        if not match:
            continue

        blogs.add(match.group(1))

for blog in blogs:
    redis.sadd("tumblr:urls", blog)
    sys.stdout.write(".")
    # print(blog)

sys.stdout.write("\n")