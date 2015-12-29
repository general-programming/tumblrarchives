from datetime import datetime, timedelta

from celery.exceptions import Retry, Reject
from celery.utils.log import get_task_logger
from sqlalchemy.exc import IntegrityError

from archives.lib.model import Post

from archives.tasks import celery, WorkerTask

logger = get_task_logger(__name__)

def cache_ids(redis, db, url):
    if redis.exists("cache:pids:" + url):
        return

    pids = [x[0] for x in db.query(Post.data['id']).filter(Post.url == url).all()]
    pipeline = redis.pipeline()
    for pid in pids:
        pipeline.sadd("cache:pids:" + url, pid)
    pipeline.expire("cache:pids:" + url, 600)  # 600 seconds = 10 minutes
    pipeline.execute()

@celery.task(base=WorkerTask)
def add_post(url, blob):
    redis = add_post.redis
    db = add_post.db

    if redis.sismember("cache:pids:" + url, blob["id"]):
        redis.incr("cache:bad:" + url)
        redis.expire("cache:bad:" + url, 60)
        return {"status": "Post %s in database." % (blob["id"])}

    try:
        db.add(Post(
            url=url,
            data=blob
        ))
        db.commit()
        redis.sadd("cache:pids:" + url, blob["id"])
    except IntegrityError as e:
        logger.error("Caught IntegrityError: %s" % (e))
        db.rollback()

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

    add_post.delay(url, tumblr.posts(url, id=post_id)["posts"])

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
        posts = tumblr.posts(url+".tumblr.com", offset=offset)['posts']
    except Exception as e:
        archive_blog.retry((url, offset, totalposts), exc=e, eta=datetime.now() + timedelta(seconds=15))

    # Archive posts
    for post in posts:
        add_post.delay(url, post)

    # Start the next task.
    archive_blog.apply_async((url, offset + 20, totalposts), eta=datetime.now() + timedelta(seconds=1))
