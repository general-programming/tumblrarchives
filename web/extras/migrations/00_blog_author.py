import sys
import time
import json

from archives.lib.connections import create_tumblr
from archives.lib.model import Post, Blog, sm
from sqlalchemy.exc import IntegrityError

sql = sm()
tungle = create_tumblr()

with open("info", "w") as f:
    for post in sql.query(Post).distinct(Post.url):
        info = tungle.blog_info(post.url)
        dumped = json.dumps({"url": post.url, "info": info})

        f.write(dumped + "\n\n")
        print(dumped)
        time.sleep(0.25)