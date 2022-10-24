import requests
from ..db import db, TopStory, NewStory
import click
from flask.cli import with_appcontext
from time import time
from os.path import exists
import asyncio
import aiohttp

# TODO: Create classes for all item types (make sure to ensure compatibilty with existing templates)

MAX_STORY_COUNT = 500
# Update items fetched from create_data().get_all_stories.().*.get_stories()
UPDATE_DB = False

# Populates database with story and comment data, used in 'create-data' flask command
async def create_data():
    stories = await get_all_stories()
    insert_stories_db(stories=stories)


# Updates database story data, used in 'get_new_api_data' APScheduler task
async def update_data():
    global UPDATE_DB
    UPDATE_DB = True
    await create_data()


# Takes in flag '--update' to update the items already in the database, if any
@click.command("create-data")
@click.option("--update", is_flag=True)
@with_appcontext
def create_data_command(update: bool):
    if exists("db/database.db"):
        click.echo("** Adding Hacker News data **")
        start = time()
        global UPDATE_DB
        UPDATE_DB = update
        asyncio.run(create_data())  # Start event loop for get_stories coroutine
        click.echo(f"* Done in {round(time() - start, 3)} seconds *")
    else:
        click.echo("Database not found. Use 'flask init-db'.")


# Called in app.py to add command to flask
def add_create_data_command(app):
    app.cli.add_command(create_data_command)


###################################################
#                                                 #
# 'query_*' functions access database.db for data #
#                                                 #
###################################################


def query_top_stories(count=1):
    return db.session.scalars(
        db.select(TopStory).order_by(TopStory.order_num).limit(count)
    ).all()


def query_new_stories(count=1):
    return db.session.scalars(
        db.select(TopStory).order_by(TopStory.time.desc()).limit(count)
    ).all()


def query_story(id):
    return db.session.scalars(db.select(TopStory).filter_by(id=id)).one_or_none()


#####################################################
#                                                   #
# 'get_*' functions access Hacker News API for data #
#                                                   #
#####################################################


async def get_all_stories():
    return [
        await get_top_stories(count=MAX_STORY_COUNT),
        await get_new_stories(count=MAX_STORY_COUNT),
    ]


async def get_top_stories(count):
    return await get_stories(
        url="https://hacker-news.firebaseio.com/v0/topstories.json",
        count=count,
        db_table="top_stories",
        db_object=TopStory,
    )


async def get_new_stories(count):
    return await get_stories(
        url="https://hacker-news.firebaseio.com/v0/newstories.json",
        count=count,
        db_table="new_stories",
    )


async def get_stories(url, count, db_table, db_object=None):
    global UPDATE_DB
    tasks, stories = [], []
    # 500 is the max items the Hacker News API returns
    count = MAX_STORY_COUNT if count > MAX_STORY_COUNT else count

    story_ids: list = requests.get(url).json()  # Fetch id's from Hacker News API

    async with aiohttp.ClientSession() as client_session:
        for story_id in story_ids[:count]:
            story_found = None
            if db_object:
                story_found = db_object.find_item(story_id)
            if (story_found and UPDATE_DB) or not story_found:
                # Create asyncio tasks made up of a coroutine
                tasks.append(
                    asyncio.create_task(
                        async_fetch_item(
                            client_session=client_session, item_id=story_id
                        )
                    )
                )
        # Run all tasks (coroutines) concurrently
        stories = await asyncio.gather(*tasks)
    return stories


async def async_fetch_item(client_session, item_id):
    res = await client_session.get(
        f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
    )
    return await res.json()


def insert_stories_db(stories):
    story_db_table_names = ["top_stories", "new_stories"]
    db.session.execute(db.delete(TopStory))  # Table is of newest top 500 stories

    for story_db_table_name, stories in zip(story_db_table_names, stories):
        for num, story in enumerate(stories):
            try:
                if story_db_table_name == "top_stories":
                    top_story = TopStory.find_item(story["id"])
                    if not top_story:
                        top_story = TopStory(
                            id=story["id"],
                            title=story["title"],
                            score=story["score"],
                            time=story["time"],
                            author=story["by"],
                            url=story["url"] if "url" in story else "",
                            order_num=num,
                        )
                        db.session.add(top_story)
                    db.session.commit()
                elif story_db_table_name == "new_stories":
                    new_story = NewStory.find_item(story["id"])
                    if not new_story:
                        new_story = NewStory(
                            id=story["id"],
                            title=story["title"],
                            score=story["score"],
                            time=story["time"],
                            author=story["by"],
                            url=story["url"] if "url" in story else "",
                        )
                        db.session.add(new_story)
                    db.session.commit()
            except:
                print(f"Couldn't insert story {num}.")
