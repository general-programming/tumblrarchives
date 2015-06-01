# This Python file uses the following encoding: utf-8
from flask import Flask
from archives.lib.requests import connect_sql, disconnect_sql
from archives.lib.assets import assets
from archives.views import main

app = Flask(__name__)

# Static assets
assets.init_app(app)

# Request handlers
app.before_request(connect_sql)
app.teardown_request(disconnect_sql)

# Blueprints
app.register_blueprint(main.blueprint)
