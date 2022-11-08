import requests
from ..db import (
    db,
    User,
    Story,
    Comment,
    StoryAssociation,
    WebsiteSetting,
)
import click
from flask.cli import with_appcontext
from time import time
from os.path import exists
import asyncio
import aiohttp
from flask_login import current_user

MAX_STORY_COUNT = 30
# Enables or disables API query and database insertion of duplicate items in database
UPDATE_DB = False
IDS_QUERIED = 0

# Populates database with story and comment data, used in 'create-data' flask command
async def create_data():
    # Insert Stories into database
    stories = await get_top_stories(count=MAX_STORY_COUNT)
    insert_stories_db(stories=stories)

    # Insert Comments into database
    if toggle := WebsiteSetting.find_item("toggle_comments"):
        if toggle.status == "true":
            comments = [
                await get_comments(story) for story in stories
            ]  # List of lists of dicts
            insert_comments_db(comments=comments)


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
    if exists("hacker_news/db/database.db"):
        click.echo("** Adding Hacker News data **")
        start = time()
        global UPDATE_DB
        UPDATE_DB = update
        asyncio.run(create_data())  # Start event loop for get_stories coroutine
        click.echo(f"* Done in {round(time() - start, 3)} seconds *")
        click.echo(f"* {IDS_QUERIED} IDs queried *")
    else:
        click.echo("Database not found. Check config.")


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
        db.select(Story).order_by(Story.order_num.desc()).limit(count)
    ).all()


def query_story(id):
    story = db.session.scalars(db.select(Story).filter_by(id=id)).one_or_none()
    return story


def query_comments(story_id):
    comments = db.session.scalars(db.select(Comment).filter_by(story_id=story_id)).all()
    return comments


def query_liked_stories(story_id):
    liked_stories = db.session.scalars(
        db.select(Comment).filter_by(story_id=story_id)
    ).all()

    return liked_stories


#####################################################
#                                                   #
# 'get_*' functions access Hacker News API for data #
#                                                   #
#####################################################


async def get_top_stories(count):
    return await get_stories(
        url="https://hacker-news.firebaseio.com/v0/topstories.json", count=count
    )


async def get_stories(url, count):
    global UPDATE_DB
    tasks, stories = [], []
    # 500 is the max items the Hacker News API returns
    count = MAX_STORY_COUNT if count > MAX_STORY_COUNT else count

    story_ids: list = requests.get(url).json()  # Fetch id's from Hacker News API

    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(verify_ssl=False)
    ) as client_session:
        for story_id in story_ids[:count]:
            story_found = Story.find_item(story_id)
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


async def get_comments(story):
    all_comments = []
    client_session = aiohttp.ClientSession()

    # The first comment will be a story
    async def fetch_comments(parent_comment):
        tasks, comments = [], []

        for comment_id in parent_comment["kids"]:
            # Create asyncioz tasks made up of a coroutine
            tasks.append(
                asyncio.create_task(
                    async_fetch_item(client_session=client_session, item_id=comment_id)
                )
            )
        # Run all tasks (coroutines) concurrently
        comments = await asyncio.gather(*tasks)

        # Check and fetch child comments
        for comment in comments:
            if comment.get("kids"):
                comment["kids"] = await fetch_comments(comment)
        return comments

    if story.get("kids"):
        all_comments = await fetch_comments(story)
    await client_session.close()

    return all_comments


# TODO: This can be a decorator?
async def async_fetch_item(client_session, item_id):
    global IDS_QUERIED
    IDS_QUERIED += 1
    res = await client_session.get(
        f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
    )
    return await res.json()


def insert_stories_db(stories):
    # Guarantees order of stories is correct
    num_story_rows = db.session.query(Story).count()

    for num, story in enumerate(stories[::-1]):
        found_story = Story.find_item(story["id"])
        if (found_story and UPDATE_DB) or not found_story:
            found_story = db.session.merge(
                Story(
                    id=story.get("id"),
                    title=story.get("title"),
                    score=story.get("score"),
                    time=story.get("time"),
                    author=story.get("by"),
                    url=story.get("url", ""),
                    order_num=num + num_story_rows,
                    num_comments=story.get("descendants", 0),
                )
            )
            db.session.add(found_story)
    db.session.commit()


def insert_comments_db(comments):
    def insert_child_comments(parent_comment, parent_comment_object):
        for comment in parent_comment["kids"]:
            # Have not been able to update comment information (SQLAlchemy's merge function is giving issues)
            found_comment = Comment.find_item(comment["id"])
            if not comment.get("dead", False) and not found_comment:
                comment = Comment(
                    id=comment.get("id"),
                    time=comment.get("time"),
                    author=comment.get("by"),
                    text=comment.get("text"),
                    type="child",
                    parent_comment=parent_comment_object,
                )
                db.session.add(comment)

                if comment.get("kids"):
                    insert_child_comments(
                        parent_comment=comment,
                        parent_comment_object=comment,
                    )

    for root_comments in comments:
        for root_comment in root_comments:
            # Have not been able to update comment information (SQLAlchemy's merge function is giving issues)
            found_comment = Comment.find_item(root_comment["id"])
            if not root_comment.get("dead", False) and not found_comment:
                comment = Comment(
                    id=root_comment.get("id"),
                    time=root_comment.get("time"),
                    author=root_comment.get("by"),
                    text=root_comment.get("text"),
                    type="root",
                    story=Story.find_item(root_comment["parent"]),
                )
                if root_comment.get("kids"):
                    insert_child_comments(
                        parent_comment=root_comment,
                        parent_comment_object=comment,
                    )
                db.session.add(comment)
    db.session.commit()
