from flask import Flask, g, render_template
from lib.requests import connect_sql, disconnect_sql
from lib.model import Post

app = Flask(__name__)

app.before_request(connect_sql)
app.teardown_request(disconnect_sql)

@app.route("/")
def front():
    urls = g.sql.query(Post.url).distinct().all()

    return render_template("front.html",
        urls=urls
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
