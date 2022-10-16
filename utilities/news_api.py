import requests
from ..db import query_db
import click
from flask.cli import with_appcontext
from time import time
from os.path import exists
import asyncio
import aiohttp

MAX_STORY_COUNT = 500

# Populates database with post and comment data, used in 'create-data' flask command
# If update == True, function will take a while to run because of API requests
async def create_data(update):
    stories = await get_stories(update)
    insert_stories_db(stories)


# Takes in flag '--update' to update the items already in the database, if any
@click.command("create-data")
@click.option("--update", is_flag=True)
@with_appcontext
def create_data_command(update):
    if exists("db/database.db"):
        click.echo("** Adding Hacker News data **")
        start = time()
        asyncio.run(create_data(update))  # Start event loop for get_stories coroutine
        click.echo(f"* Done in {round(time() - start, 3)} seconds *")
    else:
        click.echo("Database not found. Use 'flask init-db'.")


# Called in app.py to add command to flask
def add_create_data_command(app):
    app.cli.add_command(create_data_command)


def query_top_stories(count=1):
    return query_db(f"SELECT * FROM top_stories LIMIT {count}")


def query_new_stories(count=1):
    return query_db(f"SELECT * FROM new_stories LIMIT {count}")


async def get_stories(update):
    return [
        await get_top_stories(MAX_STORY_COUNT, update),
        await get_new_stories(MAX_STORY_COUNT, update),
    ]


async def get_top_stories(count=1, update=False):
    return await get_items(
        "https://hacker-news.firebaseio.com/v0/topstories.json",
        count,
        "top_stories",
        update,
    )


async def get_new_stories(count=1, update=False):
    return await get_items(
        "https://hacker-news.firebaseio.com/v0/newstories.json",
        count,
        "new_stories",
        update,
    )


async def get_items(url, count, db_table, update=False):
    # 500 is the max items the news api returns
    count = MAX_STORY_COUNT if count > MAX_STORY_COUNT else count

    async def fetch_item(client_session, item_id):
        res = await client_session.get(
            f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
        )
        return await res.json()

    async with aiohttp.ClientSession() as client_session:
        tasks, items = [], []
        item_ids: list = requests.get(url).json()  # Fetch id's from Hacker News API
        for item_id in item_ids[:count]:
            item_found = query_db(f"SELECT * FROM {db_table} WHERE id = ?", (item_id,))
            if (item_found and update) or not item_found:
                # Create asyncio tasks made up of a coroutine
                tasks.append(asyncio.create_task(fetch_item(client_session, item_id)))
        items = await asyncio.gather(*tasks)  # Run all tasks (coroutines) concurrently
    return items


def insert_stories_db(stories):
    story_db_table_names = ["top_stories", "new_stories"]

    for story_db_table_name, stories in zip(story_db_table_names, stories):
        for story in stories:
            query_db(
                f"INSERT INTO {story_db_table_name} (id, title, score, time, author, url) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    story["id"],
                    story["title"],
                    story["score"],
                    story["time"],
                    story["by"],
                    story["url"] if "url" in story else "",
                ),
            )
