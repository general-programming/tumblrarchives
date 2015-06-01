import redis
import sys
import json
from archives.lib.model import sm, Post
from sqlalchemy.exc import IntegrityError

r = redis.Redis()
sql = sm()

method = sys.argv[1]
url = sys.argv[2]

ids = set(x[0] for x in sql.query(Post.data['id']).all())

if method == "json":
    posts = json.load(open(url+".json"))
elif method == "redis":
    posts = r.lrange("blog:"+url, 0, -1)

for x in posts:
    data = json.loads(x)
    post = Post(
        url=url,
        data=data
    )
    try:
        if data['id'] not in ids:
            sql.add(post)
            print "id %s commited" % (data['id'])
            ids.add(data['id'])
            sql.commit()
        else:
            print "id %s exists" % (data['id'])
    except IntegrityError:
        print "sqlalchemy.exc.IntegrityError"
        sql.rollback()
