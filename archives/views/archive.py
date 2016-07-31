from archives.lib import Page
from archives.lib.helpers import parse_tumblr_url
from archives.lib.model import Post
from archives.tasks.tumblr import archive_post
from flask import (Blueprint, abort, g, jsonify, redirect, render_template,
                   request, url_for)
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import TEXT
from sqlalchemy.exc import DataError
from sqlalchemy.orm.exc import NoResultFound
from webhelpers.paginate import PageURL

blueprint = Blueprint('archive', __name__)

POST_TYPES = ['text', 'quote', 'link', 'answer', 'video', 'audio', 'photo', 'chat']

@blueprint.route("/")
def front():
    return render_template("front.html")

@blueprint.route("/submit", methods=["GET", "POST"])
def submit():
    parsed = parse_tumblr_url(request.form.get("url", ""))
    toast = ""

    if parsed:
        archive_post.delay(parsed["url"], parsed["post_id"])
        toast = 'Your post has been archived <a href="%s"> here</a>.' % (url_for("archive.post", postid=parsed["post_id"]))
    elif "url" in request.form:
        toast = "The URL you entered is invalid. <br> An example of a valid URL is demo.tumblr.com/post/236"

    return render_template("submit.html", toast=toast)

@blueprint.route("/post/<postid>")
def post(postid=None):
    try:
        post = g.sql.query(Post).filter(Post.data['id'] == postid).one()
    except (NoResultFound, DataError):
        abort(404)

    if 'json' in request.args:
        return jsonify(post.data)

    return render_template("post.html", post=post)

@blueprint.route("/archive/<url>")
def archive(url=None, page=1):
    if not url or not g.sql.query(Post).filter(Post.url == url).limit(1).count():
        abort(404)

    page = request.args.get('page', None)
    tag = request.args.get('tag', None)
    posttype = request.args.get('type', 'all')

    if page < 1 or not page:
        return redirect(url_for('archive.archive', url=url, page=1))

    url_for_page = PageURL(url_for("archive.archive", url=url), {"page": page})

    sql = g.sql.query(Post).filter(Post.url == url)

    if tag:
        url_for_page.params.update({"tag": tag})
        # complete tag hack because i have no idea how to filter json arrays with jsonb (lol)
        sql = sql.filter(func.lower(Post.data['tags'].cast(TEXT)).contains('"' + tag + '"'))
    elif posttype in POST_TYPES:
        url_for_page.params.update({"type": posttype})
        sql = sql.filter(Post.data['type'].astext == posttype)

    posts = Page(sql.order_by(Post.data['timestamp'].desc()), items_per_page=15, page=page, url=url_for_page)

    return render_template(
        "archive.html",
        url=url,
        posts=posts,
        tag=tag,
        posttype=posttype,
        POST_TYPES=POST_TYPES
    )
