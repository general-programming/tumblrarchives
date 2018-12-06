import sys
import time
import json

from urllib.parse import urlparse

from sqlalchemy.dialects.postgresql import insert

from archives.lib.connections import create_tumblr
from archives.lib.model import Post, Blog, sm


sql = sm()
tungle = create_tumblr()

META_POP = ["status", "msg", ""]

for post in sql.query(Post).distinct(Post.url):
    # Terrible but there's not many blogs in the DB so it can't be that bad.
    if sql.query(Blog).filter(Blog.name == post.url).scalar():
        continue

    time.sleep(0.25)
    info = tungle.blog_info(post.url)

    # Ignore 404s
    if "meta" in info:
        if info["meta"]["status"] == 404:
            print(f"{post.url} 404")
            continue

    # wot how
    if "blog" not in info:
        print(info)
        print()
        continue

    # Make a new blog
    new_blog = Blog.create_from_metadata(sql, info)
    sql.flush()

    print(f"Got info on blog {post.url}")

sql.commit()
