def get_profile(url, redis, tumblr):
    if not redis.exists("avatar:128:" + url):
        redis.setex("avatar:128:" + url, 43200, tumblr.avatar(url, size=128).get(
            "avatar_url", "https://66.media.tumblr.com/avatar_1f10fd370f1c_128.png"
        ))

    return redis.get("avatar:128:" + url)
