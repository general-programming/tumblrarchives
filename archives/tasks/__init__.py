import os
import pytumblr

from celery import Celery, Task
from classtools import reify
from redis import StrictRedis

from archives.lib.model import sm
from archives.lib.requests import redis_pool

celery = Celery("archives", include=[
    "archives.tasks.tumblr",
])

celery.config_from_object('archives.tasks.config')

class WorkerTask(Task):
    abstract = True

    @reify
    def db(self):
        return sm()

    @reify
    def redis(self):
        return StrictRedis(connection_pool=redis_pool)

    @reify
    def tumblr_client(self):
        return pytumblr.TumblrRestClient(
            os.environ.get("TUMBLR_CONSUMER_KEY"),
            os.environ.get("TUMBLR_CONSUMER_SECRET")
        )

    def after_return(self, *args, **kwargs):
        if hasattr(self, "db"):
            self.db.close()
            del self.db

        if hasattr(self, "redis"):
            del self.redis
