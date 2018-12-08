from datetime import datetime, timedelta

from archives.lib.model import Post, Blog
from archives.tasks import WorkerTask, celery
from celery.exceptions import Reject, Retry
from celery.utils.log import get_task_logger
from sqlalchemy.exc import IntegrityError

logger = get_task_logger(__name__)

def cache_ids(redis, db, url):
    if redis.exists("cache:pids:" + url):
        return

    pids = [x[0] for x in db.query(Post.tumblr_id).filter(Post.author_id == Blog.id).filter(Blog.name == url).all()]
    pipeline = redis.pipeline()
    for pid in pids:
        pipeline.sadd("cache:pids:" + url, pid)
    pipeline.expire("cache:pids:" + url, 600)  # 600 seconds = 10 minutes
    pipeline.execute()

def check_ratelimit(redis, key, max_hits=60, expire=60):
    attempts = redis.incr(key)

    if attempts >= max_hits:
        raise Retry("API rate limit. %s hits for %s." % (attempts, key))
    else:
        redis.expire(key, expire)

@celery.task(base=WorkerTask)
def add_post(blob):
    redis = add_post.redis
    db = add_post.db

    post = Post.create_from_metadata(db, blob)
    db.commit()

@celery.task(base=WorkerTask)
def archive_post(url=None, post_id=None):
    if not url or not post_id:
        raise ValueError("Blog URL parameter is missing.")

    redis = archive_post.redis
    db = archive_post.db
    tumblr = archive_post.tumblr_client

    cache_ids(redis, db, url)

    if redis.sismember("cache:pids:" + url, post_id):
        return {"error": "Post %s in database." % (post_id)}

    check_ratelimit(redis, "api_access")

    add_post.delay(tumblr.posts(url, id=post_id)["posts"][0])

@celery.task(base=WorkerTask)
def archive_blog(url=None, offset=0, totalposts=0):
    if not url:
        raise ValueError("Blog URL parameter is missing.")

    redis = archive_blog.redis
    db = archive_blog.db
    tumblr = archive_blog.tumblr_client

    cache_ids(redis, db, url)

    try:
        if int(redis.get("cache:bad:" + url)) >= 5:
            return {"status": "done"}
    except (TypeError, ValueError):
        pass

    # Check if we can access the API.
    check_ratelimit(redis, "api_access")

    # Set the counter of total blog posts.
    try:
        if totalposts == 0:
            totalposts = tumblr.blog_info(url)["blog"]["posts"]
    except KeyError:
        raise Reject("Could not get number of posts. Data: %s" % tumblr.blog_info(url))
    except Exception as e:
        archive_blog.retry(exc=e, eta=datetime.now() + timedelta(minutes=1))

    # Get the posts
    try:
        posts = tumblr.posts(url + ".tumblr.com", offset=offset)['posts']
    except Exception as e:
        archive_blog.retry((url, offset, totalposts), exc=e, eta=datetime.now() + timedelta(seconds=15))

    # Archive posts
    for post in posts:
        add_post.delay(post)

    # Start the next task.
    archive_blog.apply_async((url, offset + 20, totalposts), eta=datetime.now() + timedelta(seconds=1))
