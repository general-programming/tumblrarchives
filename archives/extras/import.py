import sys
import pytumblr
import time
from archives.lib.model import sm, Post
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
            sql.commit()
            self.ids.add(data['id'])
        except IntegrityError:
            print "sqlalchemy.exc.IntegrityError"
            sql.rollback()

blog = Blog(sys.argv[1])

# Tumblr crawling
client = pytumblr.TumblrRestClient(
    'Lo5py8ME9G1GGLVjQpKvk8LPqYIfe3L4LRxv9RialSc2wgrYxQ',
    '82sN1yPCNI7dpmqzSNPILhVEp0TR8P7Bnb6xpY3B6EX7xWIpXI',
    'B61AMygyQ4fTYMM324Nc91LCBA05hphJs68aPaWP4ijn3WhlpW',
    'DtsNK3kC5hMGRvfntiB1IUY9MhgqGmrCwaw6MbhMvAf1AXZSzL'
)

# Make the request
info = client.blog_info(blog.url)

offset = 0
bad = 0

while offset < info['blog']['posts']:
    if bad >= 5:
        print "All posts crawled. (Probarly)"
        break

    posts = client.posts(blog.url+".tumblr.com", offset=offset)['posts']
    offset += 20
    for post in posts:
        status = blog.add(post)
        if status == "indb":
            bad += 1
        print post
        print "-"*60
    print "%s/%s" % (offset, info['blog']['posts'])
    print "-"*60
    time.sleep(0.5)
