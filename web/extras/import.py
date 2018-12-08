import os
import sys
import time
import datetime
import threading
import collections
import traceback
import random

from sqlalchemy import or_
from sqlalchemy.sql.expression import func
from sqlalchemy.exc import IntegrityError

from archives import sentry_sdk
from archives.lib.connections import create_tumblr
from archives.lib.model import Post, Blog, sm, session_scope


class BlogManager(object):
    def __init__(self):
        self.tumblr = create_tumblr()
        self.db = sm()
        self.grabbed = collections.defaultdict(lambda: 0)
        self.bad = collections.defaultdict(lambda: 0)

        self.queue = []
        self.running = True

    def log(self, *args):
        print(f"[{threading.current_thread().name}]", *args)

    @staticmethod
    def add(db, data, oldest=None):
        if not oldest:
            oldest = datetime.datetime.fromtimestamp(0)

        post = Post.create_from_metadata(db, data)
        db.add(post)
        if oldest > post.posted:
            return False

        return True

    def archive(self, blog: str):
        if isinstance(blog, str):
            info = self.tumblr.blog_info(blog)
            blog = Blog.create_from_metadata(self.db, info)
        else:
            info = self.tumblr.blog_info(blog.name)

        if info.get("meta", {}).get("status", None) == 503:
            self.log(info)

        for offset in range(0, info['blog']['posts'] + 20, 20):
            self.queue.append({
                "name": blog.name,
                "offset": offset,
                "last_crawl": blog.last_crawl_update,
                "total_posts": info["blog"]["posts"],
            })

        blog.last_crawl_update = blog.updated
        self.db.commit()

    def random(self):
        while self.running:
            if len(self.queue) > 0:
                time.sleep(1)
                continue

            random_blog = self.db.query(Blog).filter(or_(
                Blog.updated != Blog.last_crawl_update,
                Blog.last_crawl_update == None
            )).order_by(func.random()).limit(1).scalar()
    
            self.log(random_blog.name, random_blog.total_posts)
            self.archive(random_blog)

    def smallest_to_largest(self):
        while self.running:
            if len(self.queue) > 8:
                time.sleep(1)
                continue

            blogs = self.db.query(Blog).filter(or_(
                Blog.updated != Blog.last_crawl_update,
                Blog.last_crawl_update == None
            )).filter(Blog.total_posts > 0).order_by(Blog.total_posts).limit(8).all()

            for blog in blogs:
                self.log(blog.name, blog.total_posts, len(self.queue))
                self.archive(blog)

    def process(self, name, offset, last_crawl, total_posts):
        with session_scope() as db:
            if self.bad[name] >= 5:
                if self.bad[name] != 999:
                    self.log(f"All posts crawled for {name}. (Probarly)")
                    self.bad[name] = 999
                return

            # Get posts of the offset.
            posts_response = self.tumblr.posts(name, offset=offset)
            if posts_response.get("meta", {}).get("status", None) == 503:
                self.log(posts_response)
                return

            # Add the posts one by one.
            posts = posts_response["posts"]
            for post in posts:
                post_ok = self.add(db, post, last_crawl)
                self.grabbed[name] += 1
                if not post_ok:
                    self.bad[name] += 1
                    continue

            db.commit()
            self.log(f"{total_posts - self.grabbed[name]} posts remaining for blog '{name}'")

    def processor(self):
        while self.running or len(self.queue) > 0:
            if len(self.queue) == 0:
                time.sleep(1)
                continue

            item = self.queue.pop(random.randrange(len(self.queue)))

            try:
                self.process(item["name"], item["offset"], item["last_crawl"], item["total_posts"])
            except:
                if sentry_sdk:
                    sentry_sdk.capture_exception()
                traceback.print_exc()

if __name__ == "__main__":
    workers = []
    adder_thread = None
    blog_manager = BlogManager()
    blog_to_archive = sys.argv[1]
    
    if blog_to_archive == "random":
        adder_thread = threading.Thread(target=blog_manager.random)
    elif blog_to_archive == "smallest_to_largest":
        adder_thread = threading.Thread(target=blog_manager.smallest_to_largest)
    else:
        blog_manager.archive(sys.argv[1])

    # Add the adder thread if set.
    if adder_thread:
        adder_thread.start()
        workers.append(adder_thread)

    # Thread startup
    for x in range(0, int(os.environ.get("WORKERS", 4))):
        t = threading.Thread(target=blog_manager.processor)
        t.start()
        workers.append(t)

    try:
        while blog_manager.running:
            # If the adder is dead, stop running.
            if adder_thread and not adder_thread.is_alive():
                blog_manager.running = False

            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping!")
        blog_manager.running = False

    if adder_thread:
        adder_thread.join()

    for t in workers:
        t.join()
