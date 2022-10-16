import requests
from ..db import query_db
import click
from flask.cli import with_appcontext
from time import time
from os.path import exists

MAX_STORY_COUNT = 500

# Populates database with post and comment data, used in 'create-data' flask command
# If update == True, function will take a while to run because of API requests
def create_data(update):
    story_types = ["top_stories", "new_stories"]
    stories = [
        query_top_stories(MAX_STORY_COUNT, update),
        query_new_stories(MAX_STORY_COUNT, update),
    ]

    for story_type, stories in zip(story_types, stories):
        for story in stories:
            query_db(
                f"INSERT INTO {story_type} (id, title, score, time, author, url) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    story["id"],
                    story["title"],
                    story["score"],
                    story["time"],
                    story["by"],
                    story["url"] if "url" in story else "",
                ),
            )


# Takes in flag '--update' to update the items already in the database, if any
@click.command("create-data")
@click.option("--update", is_flag=True)
@with_appcontext
def create_data_command(update):
    if exists("db/database.db"):
        click.echo("** Adding Hacker News data **")
        start = time()
        create_data(update)
        click.echo(f"* Done in {round(time() - start, 3)} seconds *")
    else:
        click.echo("Database not found. Use 'flask init-db'.")


# Called in app.py to add command to flask
def add_create_data_command(app):
    app.cli.add_command(create_data_command)


def get_top_stories(count=1):
    return query_db(f"SELECT * FROM top_stories LIMIT {count}")


def get_new_stories(count=1):
    return query_db(f"SELECT * FROM new_stories LIMIT {count}")


def query_top_stories(count=1, update=False):
    return query_items(
        "https://hacker-news.firebaseio.com/v0/topstories.json",
        count,
        "top_stories",
        update,
    )


def query_new_stories(count=1, update=False):
    return query_items(
        "https://hacker-news.firebaseio.com/v0/newstories.json",
        count,
        "new_stories",
        update,
    )


def query_items(url, count, db_table, update=False):
    # 500 is the max items the news api returns
    count = MAX_STORY_COUNT if count > MAX_STORY_COUNT else count

    items = []
    item_ids: list = requests.get(url).json()
    for item_id in item_ids[:count]:
        item_found = query_db(f"SELECT * FROM {db_table} WHERE id = ?", (item_id,))
        if (item_found and update) or not item_found:
            items.append(
                requests.get(
                    f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
                ).json()
            )

    return items
