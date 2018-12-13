import re
import gzip
import sys
import glob

from redis import StrictRedis
from archives.lib.connections import redis_pool

redis = StrictRedis(connection_pool=redis_pool)
blogs = set()

def load_file(filename: str):
    opener = open

    if filename.endswith(".gzip"):
        opener = gzip.open

    with opener(filename, "r") as f:
        for line in f:
            try:
                line = line.decode("utf8")
            except AttributeError:
                pass

            # AT format
            try:
                blogs.add(line.split("tumblr-blog:")[1])
            except IndexError:
                pass

            # Try URL match first.
            match = re.search(r"://([\w\d]+\.tumblr.com)", line)
            if match:
                blogs.add(match.group(1))

# Glob all AT files
for x in glob.glob("archiveteam-items/ADDED/*.txt"):
    load_file(x)

for blog in blogs:
    redis.sadd("tumblr:urls", blog.strip())
    sys.stdout.write(".")
    # print(blog)

sys.stdout.write("\n")