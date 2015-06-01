from webhelpers.paginate import PageURL
from flask import Blueprint, request, render_template, g, url_for, jsonify, redirect
from sqlalchemy.dialects.postgresql import TEXT
from sqlalchemy.exc import DataError
from sqlalchemy.orm.exc import NoResultFound

from archives.lib.model import Post
from archives.lib.classes import Page

import json

blueprint = Blueprint('main', __name__)

# prettyjson filter
def prettyjson(data):
    return json.dumps(data, indent=4)

blueprint.add_app_template_filter(prettyjson)

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
