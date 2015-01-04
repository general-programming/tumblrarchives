from flask import Flask, g, render_template
from lib.requests import connect_sql, disconnect_sql

app = Flask(__name__)

app.before_request(connect_sql)
app.teardown_request(disconnect_sql)

@app.route("/")
def front():
    return render_template("front.html")

if __name__ == "__main__":
    app.run(port=5000, debug=True)
