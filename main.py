# This Python file uses the following encoding: utf-8
from flask import (
    Flask,
    g,
    redirect,
    url_for,
    render_template,
    request,
    jsonify
)

from flask.ext.assets import Environment

from lib.requests import (
    connect_sql,
    disconnect_sql
)

from lib.model import Post
from lib.classes import Page
from webhelpers.paginate import PageURL
from sqlalchemy.dialects.postgresql import TEXT
from sqlalchemy.exc import DataError
from sqlalchemy.orm.exc import NoResultFound

app = Flask(__name__)

# Static assets
assets = Environment(app)
assets.from_yaml("assets.yaml")

# Request handlers
app.before_request(connect_sql)
app.teardown_request(disconnect_sql)

@app.route("/")
def front():
    urls = g.sql.query(Post.url).distinct().all()

    return render_template("front.html", urls=urls)

@app.route("/post/<postid>")
def post(postid=None):
    try:
        post = g.sql.query(Post).filter(Post.data['id'] == postid).one()
    except (NoResultFound, DataError):
        return redirect(url_for('front'))

    if 'json' in request.args:
        return jsonify(post.data)

    return render_template("post.html", post=post)

@app.route("/archive/<url>")
def archive(url=None, page=1):
    if not url or not g.sql.query(Post).filter(Post.url == url).limit(1).count():
        return redirect(url_for('front'))

    page = request.args.get('page', 1)
    tag = request.args.get('tag', None)

    if page < 1:
        return redirect(url_for('archive', page=1))

    url_for_page = PageURL(url_for("archive", url=url), {"page": page})

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
