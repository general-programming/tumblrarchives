import os

from archives.lib.requests import redis_pool

# Debug
if 'DEBUG' in os.environ:
    CELERY_REDIRECT_STDOUTS_LEVEL = "DEBUG"

# Broker and Result backends
BROKER_URL = os.environ.get("CELERY_BROKER", "redis://%s:%s/0" % (
    redis_pool.connection_kwargs["host"],
    redis_pool.connection_kwargs["port"]
))

CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT", "redis://%s:%s/0" % (
    redis_pool.connection_kwargs["host"],
    redis_pool.connection_kwargs["port"]
))

# Time
CELERY_TIMEZONE = "UTC"
CELERY_ENABLE_UTC = True
CELERY_TASK_RESULT_EXPIRES = 21600  # 21600 seconds = 6 hours

# Logging
CELERY_STORE_ERRORS_EVEN_IF_IGNORED = True

# Serialization
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]

# Performance
CELERYD_PREFETCH_MULTIPLIER = 1
CELERY_DISABLE_RATE_LIMITS = True
