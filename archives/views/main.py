from webhelpers.paginate import PageURL
from flask import Blueprint, request, render_template, g, url_for, jsonify, redirect
from sqlalchemy.dialects.postgresql import TEXT
from sqlalchemy import func
from sqlalchemy.exc import DataError
from sqlalchemy.orm.exc import NoResultFound

from archives.lib import Page
from archives.lib.model import Post
from archives.lib.helpers import parse_tumblr_url

import json
from datetime import datetime

blueprint = Blueprint('main', __name__)

POST_TYPES = ['text', 'quote', 'link', 'answer', 'video', 'audio', 'photo', 'chat']

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

@blueprint.route("/submit", methods=["GET", "POST"])
def submit():
    if 'url' in request.form:
        parsed = parse_tumblr_url(request.form["url"])
        return str(parsed)

    return render_template("submit.html")

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
    posttype = request.args.get('type', 'all')

    if page < 1 or not page:
        return redirect(url_for('main.archive', url=url, page=1))

    url_for_page = PageURL(url_for("main.archive", url=url), {"page": page})

    sql = g.sql.query(Post).filter(Post.url == url)

    if tag:
        url_for_page.params.update({"tag": tag})
        # complete tag hack because i have no idea how to filter json arrays with jsonb (lol)
        sql = sql.filter(func.lower(Post.data['tags'].cast(TEXT)).contains('"' + tag + '"'))
    elif posttype in POST_TYPES:
        url_for_page.params.update({"type": posttype})
        sql = sql.filter(Post.data['type'].astext == posttype)

    posts = Page(sql.order_by(Post.data['timestamp'].desc()), items_per_page=15, page=page, url=url_for_page)

    return render_template("archive.html",
        url=url,
        posts=posts,
        tag=tag,
        posttype=posttype,
        POST_TYPES=POST_TYPES
    )
