import re

validate_url = re.compile(r"([-\w]+).tumblr.com/post/(\d+)", re.I | re.U)

def parse_tumblr_url(url=None):
    if not url:
        return None

    if url.startswith("-") or url.endswith("-"):
        return None

    matches = validate_url.search(url)

    if matches:
        return {
            "url": matches.group(1),
            "post_id": matches.group(2)
        }

    return None
