from redis import StrictRedis
from archives.lib.connections import redis_pool

redis = StrictRedis(connection_pool=redis_pool)
files = ["maybe_dead_nsfw_tumblrs.txt", "nsfw_tumblrs.txt"]

for file in files:
    with open(file, "r") as f:
        for line in f:
            split_line = line.split(" ")
            redis.sadd("tumblr:urls", split_line[-1].strip().lstrip("www."))