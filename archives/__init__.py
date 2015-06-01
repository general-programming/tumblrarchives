# This Python file uses the following encoding: utf-8
from flask import Flask
from archives.lib.requests import connect_sql, disconnect_sql
from archives.views import main

app = Flask(__name__)

# Request handlers
app.before_request(connect_sql)
app.teardown_request(disconnect_sql)

# Blueprints
app.register_blueprint(main.blueprint)
