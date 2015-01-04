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

from flask.ext.assets import (
    Environment,
    Bundle
)

from lib.requests import (
    connect_sql,
    disconnect_sql
)

from lib.model import Post
from lib.classes import Page
from webhelpers.paginate import PageURL
from sqlalchemy.exc import DataError
from sqlalchemy.orm.exc import NoResultFound
import os

app = Flask(__name__)

# Debug
app.config['DEBUG'] = os.environ.get('DEBUG', False)

# Static assets
assets = Environment(app)
assets.from_yaml("assets.yaml")


app.before_request(connect_sql)
app.teardown_request(disconnect_sql)

@app.route("/")
def front():
    urls = g.sql.query(Post.url).distinct().all()

    return render_template("front.html",
        urls=urls
    )

@app.route("/post/<postid>")
def post(postid=None):
    try:
        post = g.sql.query(Post).filter(Post.data['id'] == postid).one()
    except (NoResultFound, DataError):
        return redirect(url_for('front'))

    if 'json' in request.args:
        return jsonify(post.data)

    return render_template("post.html",
        post=post
    )

@app.route("/archive/<url>")
def archive(url=None, page=1):
    if not url or not g.sql.query(Post).filter(Post.url == url).limit(1).count():
        return redirect(url_for('front'))

    page = request.args.get('page', 1)
    tag = request.args.get('tag', None)

    if page < 1:
        return redirect(url_for('archive', page=1))

    url_for_page = PageURL(url_for("archive", url=url), {"page": page})
    posts = Page(g.sql.query(Post).filter(Post.url == url).order_by(Post.data['timestamp'].desc()), page=page, url=url_for_page)

    return render_template("archive.html",
        url=url,
        posts=posts
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
