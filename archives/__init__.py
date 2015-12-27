# This Python file uses the following encoding: utf-8
from flask import Flask
from archives.lib.requests import connect_sql, before_request, disconnect_sql, cache_breaker
from archives.views import main

app = Flask(__name__)

# Throw tracebacks to console
app.config['PROPAGATE_EXCEPTIONS'] = True

# Cache breaking
app.url_defaults(cache_breaker)

# Request handlers
app.before_request(connect_sql)
app.before_request(before_request)
app.teardown_request(disconnect_sql)

# Blueprints
app.register_blueprint(main.blueprint)
