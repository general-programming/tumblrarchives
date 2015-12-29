# This Python file uses the following encoding: utf-8
from flask import Flask
from archives.lib.requests import connect_sql, connect_redis, before_request, disconnect_sql, disconnect_redis, cache_breaker
from archives.views import main

app = Flask(__name__)

# Throw tracebacks to console
app.config['PROPAGATE_EXCEPTIONS'] = True

# Cache breaking
app.url_defaults(cache_breaker)

# Request handlers
app.before_request(connect_sql)
app.before_request(connect_redis)
app.before_request(before_request)
app.teardown_request(disconnect_sql)
app.teardown_request(disconnect_redis)

# Blueprints
app.register_blueprint(main.blueprint)
