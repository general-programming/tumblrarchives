import sys
import time

from archives.lib.connections import create_tumblr
from archives.lib.model import Post, sm
from sqlalchemy.exc import IntegrityError

sql = sm()

class Blog(object):
    def __init__(self, url):
        self.url = url
        self.ids = set(x[0] for x in sql.query(Post.data['id']).filter(Post.url == self.url).all())

    def add(self, data):
        if data['id'] in self.ids:
            print "ID {id} in database.".format(
                id=data['id']
            )

            return "indb"

        post = Post(
            url=self.url,
            data=data
        )

        try:
            sql.add(post)
            self.ids.add(data['id'])
        except IntegrityError as e:
            print("IntegrityError")
            print(str(e))
            sql.rollback()

blog = Blog(sys.argv[1])

# Tumblr crawling
client = create_tumblr()

# Make the request
info = client.blog_info(blog.url)

bad = 0

for offset in xrange(0, info['blog']['posts'] + 20, 20):
    if bad >= 5:
        print "All posts crawled. (Probarly)"
        break

    posts = client.posts(blog.url + ".tumblr.com", offset=offset)['posts']
    for post in posts:
        status = blog.add(post)
        if status == "indb":
            bad += 1
            continue
    sql.commit()
    print "%s/%s" % (offset, info['blog']['posts'])
    time.sleep(0.25)

sql.close()
