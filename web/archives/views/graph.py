import json

from archives.lib.model import Post
from archives.lib.utils import get_profile
from flask import (Blueprint, abort, g, jsonify, redirect, render_template,
                   request)
from sqlalchemy.orm.exc import NoResultFound

blueprint = Blueprint('graph', __name__)


def generate_post_graph(post):
    # XXX post.url remove
    if g.redis.exists("viscache:" + post.url):
        return json.loads(g.redis.get("viscache:" + post.url))

    blogs = post.get_linked_blogs()
    top_id = 1
    current_id = 1
    nodes = [{"id": 1, "label": post.url, "shape": "circularImage", "image": get_profile(post.url, g.redis, g.tumblr)}]
    edges = []

    for blog in blogs:
        current_id = current_id + 1
        nodes.append({
            "id": current_id,
            "label": blog,
            "shape": "circularImage",
            "image": get_profile(blog, g.redis, g.tumblr)
        })
        edges.append({
            "from": top_id,
            "to": current_id
        })

    vis = {
        "nodes": nodes,
        "edges": edges
    }

    g.redis.setex("viscache:" + post.url, 3600, json.dumps(vis))

    return vis

@blueprint.route("/<author_name>/users")
def graph(author_name=None):
    try:
        post = g.sql.query(Post).filter(Blog.name == author_name).filter(Post.author_id == Blog.id).limit(1).one()
    except NoResultFound:
        return abort(404)

    if "json" in request.args:
        return jsonify(list(post.get_linked_blogs()))

    data = generate_post_graph(post)

    return render_template("graph_posts.html", data=data)
