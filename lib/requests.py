# This Python file uses the following encoding: utf-8
from .model import sm
from flask import g

def connect_sql():
    g.sql = sm()

def disconnect_sql(result=None):
    g.sql.close()
    del g.sql
    return result
