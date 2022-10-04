import sqlite3

import click
from flask import current_app, g


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect("database.sql")
        g.db.row_factory = sqlite3.Row  # Rows are returns as dicts

    return g.db


def close_db(e=None):
    db = g.pop("db", None)

    if db is not None:
        db.close()


def init_db():
    db = get_db()

    with current_app.open_resource("api/schema.sql") as schema_file:
        db.executescript(schema_file.read().decode("utf8"))


# Used to add CLI flag 'init-db' for flask tool
@click.command("init-db")
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo("Initialized the database.")


# Called in app.py
def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
