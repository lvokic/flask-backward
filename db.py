from flask import g
import sqlite3
import os

BASE_DIR = os.path.join(os.path.dirname(__file__), 'database')
DB_PATH = os.path.join(BASE_DIR, "assignments.db")

def close_db(e=None):
    db = g.pop('db', None)
    cursor = g.pop('cursor', None)

    if cursor is not None:
        cursor.close()
    if db is not None:
        db.close()