# This Python file uses the following encoding: utf-8
import os
import traceback

from flask import Flask, request, render_template
from archives.lib.requests import set_cookie, check_csrf_token, connect_sql, connect_redis, before_request, disconnect_sql, disconnect_redis, cache_breaker
from archives.views import main
from archives.lib.extensions import inject_extensions

app = Flask(__name__)

# Throw tracebacks to console
app.config['PROPAGATE_EXCEPTIONS'] = True

if 'DEBUG' in os.environ:
    app.config['DEBUG'] = True

# Inject Jinja defaults
inject_extensions(app)

# Cache breaking
app.url_defaults(cache_breaker)

# Request handlers
app.before_request(connect_sql)
app.before_request(connect_redis)
app.before_request(check_csrf_token)
app.before_request(before_request)
app.after_request(set_cookie)
app.teardown_request(disconnect_sql)
app.teardown_request(disconnect_redis)

# Blueprints
app.register_blueprint(main.blueprint)

# Error handlers
@app.errorhandler(404)
def notfound_error(e):
    return render_template("errors/404.html"), 404

if not app.config['DEBUG']:
    @app.errorhandler(Exception)
    def production_error(e):
        if request.is_xhr:
            if 'debug' not in request.args and 'debug' not in request.form:
                raise

        traceback.print_exc()

        return render_template("errors/exception.html",
            traceback=traceback.format_exc()
        ), 500
