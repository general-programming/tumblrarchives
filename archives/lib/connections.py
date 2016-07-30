import os

import pytumblr


def create_tumblr():
    return pytumblr.TumblrRestClient(
        os.environ.get("TUMBLR_CONSUMER_KEY"),
        os.environ.get("TUMBLR_CONSUMER_SECRET")
    )
