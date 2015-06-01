#!/usr/bin/env python
# This Python file uses the following encoding: utf-8
import pytumblr
import json
import redis
import time
import sys
import os

r = redis.Redis(host=os.environ['REDIS_HOST'], port=int(os.environ['REDIS_PORT']), db=int(os.environ['REDIS_DB']))

# Authenticate via OAuth
client = pytumblr.TumblrRestClient(
    'Lo5py8ME9G1GGLVjQpKvk8LPqYIfe3L4LRxv9RialSc2wgrYxQ',
    '82sN1yPCNI7dpmqzSNPILhVEp0TR8P7Bnb6xpY3B6EX7xWIpXI',
    'B61AMygyQ4fTYMM324Nc91LCBA05hphJs68aPaWP4ijn3WhlpW',
    'DtsNK3kC5hMGRvfntiB1IUY9MhgqGmrCwaw6MbhMvAf1AXZSzL'
)

# Make the request
blog = sys.argv[1]
info = client.blog_info(blog)

offset = 0

while offset < info['blog']['posts']:
    postdata = client.posts(blog+".tumblr.com", offset=offset)['posts']
    offset += 20
    for x in postdata:
        r.rpush("blog:"+blog, json.dumps(x))
        print x
        print "-"*60
    print "%s/%s" % (offset, info['blog']['posts'])
    print "-"*60
    time.sleep(0.5)
