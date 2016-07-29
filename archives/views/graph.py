from archives.lib.model import Post
from flask import Blueprint, g, jsonify, redirect, render_template, request, abort
from sqlalchemy.orm.exc import NoResultFound
from bs4 import BeautifulSoup
import json


blueprint = Blueprint('graph', __name__)

TEXT_KEYS = ["caption", "body", "content", "tree_html"]

def get_links(url):
    links = set()
    blogs = set()

    # Find links
    for post in g.sql.query(Post).filter(Post.url == url):
        for key in TEXT_KEYS:
            content = post.data.get(key, "").strip()
            if not content:
                continue

            soup = BeautifulSoup(content, "html5lib")
            for link in soup.find_all("a"):
                try:
                    links.add(link["href"])
                except KeyError:
                    pass

    # Convert links to Tumblr URLs
    for link in links:
        if "tumblr.com" not in link:
            continue
        blogs.add(link.split(".")[0].lstrip("http://").lstrip("https://"))

    return blogs


def get_profile(url):
    if not g.redis.exists("avatar:128:" + url):
        g.redis.setex("avatar:128:" + url, 43200, g.tumblr.avatar(url, size=128).get(
            "avatar_url", "https://66.media.tumblr.com/avatar_1f10fd370f1c_128.png"
        ))

    return g.redis.get("avatar:128:" + url)


def generate_post_graph(url):
    if g.redis.exists("viscache:" + url):
        return json.loads(g.redis.get("viscache:" + url))

    blogs = get_links(url)
    top_id = 1
    current_id = 1
    nodes = [{"id": 1, "label": url, "shape": "circularImage", "image": get_profile(url)}]
    edges = []

    for blog in blogs:
        current_id = current_id + 1
        nodes.append({
            "id": current_id,
            "label": blog,
            "shape": "circularImage",
            "image": get_profile(blog)
        })
        edges.append({
            "from": top_id,
            "to": current_id
        })

    vis = {
        "nodes": nodes,
        "edges": edges
    }

    g.redis.setex("viscache:" + url, 3600, json.dumps(vis))

    return vis

@blueprint.route("/<url>/users")
def graph(url=None):
    try:
        g.sql.query(Post).filter(Post.url == url).limit(1).one()
    except NoResultFound:
        return abort(404)

    if "json" in request.args:
        return jsonify(get_links())

    data = generate_post_graph(url)

    return render_template("graph_posts.html", data=data)
