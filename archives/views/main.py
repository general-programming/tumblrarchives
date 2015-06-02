from webhelpers.paginate import PageURL
from flask import Blueprint, request, render_template, g, url_for, jsonify, redirect
from sqlalchemy.dialects.postgresql import TEXT
from sqlalchemy.exc import DataError
from sqlalchemy.orm.exc import NoResultFound

from archives.lib.model import Post
from archives.lib import Page

import json
from datetime import datetime

blueprint = Blueprint('main', __name__)

# prettyjson filter
def prettyjson(data):
    return json.dumps(data, indent=4)

def prettydate(time=False):
    """
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc
    """
    now = datetime.now()
    if type(time) is int:
        diff = now - datetime.fromtimestamp(time)
    elif isinstance(time, datetime):
        diff = now - time
    elif not time:
        diff = now - now
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return str(second_diff) + " seconds ago"
        if second_diff < 120:
            return "a minute ago"
        if second_diff < 3600:
            return str(second_diff / 60) + " minutes ago"
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return str(second_diff / 3600) + " hours ago"
    if day_diff == 1:
        return "Yesterday"
    if day_diff < 7:
        return str(day_diff) + " days ago"
    if day_diff < 31:
        return str(day_diff / 7) + " weeks ago"
    if day_diff < 365:
        return str(day_diff / 30) + " months ago"
    return str(day_diff / 365) + " years ago"

blueprint.add_app_template_filter(prettyjson)
blueprint.add_app_template_filter(prettydate)

@blueprint.route("/")
def front():
    return render_template("front.html")

@blueprint.route("/post/<postid>")
def post(postid=None):
    try:
        post = g.sql.query(Post).filter(Post.data['id'] == postid).one()
    except (NoResultFound, DataError):
        return redirect(url_for('main.front'))

    if 'json' in request.args:
        return jsonify(post.data)

    return render_template("post.html", post=post)

@blueprint.route("/archive/<url>")
def archive(url=None, page=1):
    if not url or not g.sql.query(Post).filter(Post.url == url).limit(1).count():
        return redirect(url_for('main.front'))

    page = request.args.get('page', None)
    tag = request.args.get('tag', None)

    if page < 1 or not page:
        return redirect(url_for('main.archive', url=url, page=1))

    url_for_page = PageURL(url_for("main.archive", url=url), {"page": page})

    if tag:
        url_for_page.params.update({"tag": tag})
        # complete tag hack because i have no idea how to filter json arrays with jsonb (lol)
        sql = g.sql.query(Post).filter(Post.url == url).filter(Post.data['tags'].cast(TEXT).contains('"' + tag + '"')).order_by(Post.data['timestamp'].desc())
    else:
        sql = g.sql.query(Post).filter(Post.url == url).order_by(Post.data['timestamp'].desc())

    posts = Page(sql, items_per_page=15, page=page, url=url_for_page)

    return render_template("archive.html",
        url=url,
        posts=posts,
        tag=tag
    )
