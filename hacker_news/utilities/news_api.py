import requests
from ..db import (
    db,
    User,
    TopStory,
    NewStory,
    TopComment,
    NewComment,
    TopStoryAssociation,
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
    top_stories, new_stories = await get_all_stories()
    insert_stories_db(top_stories=top_stories, new_stories=new_stories)

    # Insert Comments into database
    if toggle := WebsiteSetting.find_item("toggle_comments"):
        if toggle.status == "true":
            top_comments = [
                await get_comments(top_story) for top_story in top_stories
            ]  # List of lists of dicts
            new_comments = [
                await get_comments(new_story) for new_story in new_stories
            ]  # List of lists of dicts
            insert_comments_db(top_comments=top_comments, new_comments=new_comments)


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
        db.select(TopStory).order_by(TopStory.order_num.desc()).limit(count)
    ).all()


def query_new_stories(count=1):
    return db.session.scalars(
        db.select(NewStory).order_by(NewStory.time.desc()).limit(count)
    ).all()


def query_story(id):
    top_story = db.session.scalars(db.select(TopStory).filter_by(id=id)).one_or_none()
    new_story = db.session.scalars(db.select(NewStory).filter_by(id=id)).one_or_none()

    return top_story or new_story


def query_comments(story_id):
    top_comments = db.session.scalars(
        db.select(TopComment).filter_by(story_id=story_id)
    ).all()
    new_comments = db.session.scalars(
        db.select(NewComment).filter_by(story_id=story_id)
    ).all()

    return top_comments or new_comments


def query_liked_stories(story_id):
    liked_top_stories = db.session.scalars(
        db.select(TopComment).filter_by(story_id=story_id)
    ).all()
    liked_new_stories = db.session.scalars(
        db.select(NewComment).filter_by(story_id=story_id)
    ).all()

    return liked_top_stories or liked_new_stories


#####################################################
#                                                   #
# 'get_*' functions access Hacker News API for data #
#                                                   #
#####################################################


async def get_all_stories():
    return await get_top_stories(count=MAX_STORY_COUNT), await get_new_stories(
        count=MAX_STORY_COUNT
    )


async def get_top_stories(count):
    return await get_stories(
        url="https://hacker-news.firebaseio.com/v0/topstories.json",
        count=count,
        db_object=TopStory,
    )


async def get_new_stories(count):
    return await get_stories(
        url="https://hacker-news.firebaseio.com/v0/newstories.json",
        count=count,
        db_object=NewStory,
    )


async def get_stories(url, count, db_object=None):
    global UPDATE_DB
    tasks, stories = [], []
    # 500 is the max items the Hacker News API returns
    count = MAX_STORY_COUNT if count > MAX_STORY_COUNT else count

    story_ids: list = requests.get(url).json()  # Fetch id's from Hacker News API

    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(verify_ssl=False)
    ) as client_session:
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


def insert_stories_db(top_stories, new_stories):
    # Guarantees order of top stories is correct
    num_top_story_rows = db.session.query(TopStory).count()

    for num, story in enumerate(top_stories[::-1]):
        top_story = TopStory.find_item(story["id"])
        if (top_story and UPDATE_DB) or not top_story:
            top_story = db.session.merge(
                TopStory(
                    id=story.get("id"),
                    title=story.get("title"),
                    score=story.get("score"),
                    time=story.get("time"),
                    author=story.get("by"),
                    url=story.get("url", ""),
                    order_num=num + num_top_story_rows,
                    num_comments=story.get("descendants", 0),
                )
            )
            db.session.add(top_story)

    for story in new_stories:
        new_story = NewStory.find_item(story["id"])
        if (new_story and UPDATE_DB) or not new_story:
            new_story = db.session.merge(
                NewStory(
                    id=story.get("id"),
                    title=story.get("title"),
                    score=story.get("score"),
                    time=story.get("time"),
                    author=story.get("by"),
                    url=story.get("url", ""),
                    num_comments=story.get("descendants", 0),
                )
            )
            db.session.add(new_story)

    db.session.commit()


def insert_comments_db(top_comments, new_comments):
    def insert_child_top_comments(parent_top_comment, parent_top_comment_object):
        for comment in parent_top_comment["kids"]:
            # Have not been able to update comment information (SQLAlchemy's merge function is giving issues)
            top_comment = TopComment.find_item(comment["id"])
            if not comment.get("dead", False) and not top_comment:
                top_comment = TopComment(
                    id=comment.get("id"),
                    time=comment.get("time"),
                    author=comment.get("by"),
                    text=comment.get("text"),
                    type="child",
                    parent_comment=parent_top_comment_object,
                )
                db.session.add(top_comment)

                if comment.get("kids"):
                    insert_child_top_comments(
                        parent_top_comment=comment,
                        parent_top_comment_object=top_comment,
                    )

    def insert_child_new_comments(parent_new_comment, parent_new_comment_object):
        for comment in parent_new_comment["kids"]:
            # Have not been able to update comment information (SQLAlchemy's merge function is giving issues)
            new_comment = NewComment.find_item(comment["id"])
            if not comment.get("dead", False) and not new_comment:
                new_comment = NewComment(
                    id=comment.get("id"),
                    time=comment.get("time"),
                    author=comment.get("by"),
                    text=comment.get("text"),
                    type="child",
                    parent_comment=parent_new_comment_object,
                )
                db.session.add(new_comment)

                if comment.get("kids"):
                    insert_child_new_comments(
                        parent_new_comment=comment,
                        parent_new_comment_object=new_comment,
                    )

    for root_top_comments in top_comments:
        for root_top_comment in root_top_comments:
            # Have not been able to update comment information (SQLAlchemy's merge function is giving issues)
            top_comment = TopComment.find_item(root_top_comment["id"])
            if not root_top_comment.get("dead", False) and not top_comment:
                top_comment = TopComment(
                    id=root_top_comment.get("id"),
                    time=root_top_comment.get("time"),
                    author=root_top_comment.get("by"),
                    text=root_top_comment.get("text"),
                    type="root",
                    story=TopStory.find_item(root_top_comment["parent"]),
                )
                if root_top_comment.get("kids"):
                    insert_child_top_comments(
                        parent_top_comment=root_top_comment,
                        parent_top_comment_object=top_comment,
                    )
                db.session.add(top_comment)

    for root_new_comments in new_comments:
        for root_new_comment in root_new_comments:
            # Have not been able to update comment information (SQLAlchemy's merge function is giving issues)
            new_comment = NewComment.find_item(root_new_comment["id"])
            if not root_new_comment.get("dead", False) and not new_comment:
                new_comment = NewComment(
                    id=root_new_comment.get("id"),
                    time=root_new_comment.get("time"),
                    author=root_new_comment.get("by"),
                    text=root_new_comment.get("text"),
                    type="root",
                    story=NewStory.find_item(root_new_comment["parent"]),
                )
                if root_new_comment.get("kids"):
                    insert_child_new_comments(
                        parent_new_comment=root_new_comment,
                        parent_new_comment_object=new_comment,
                    )
                db.session.add(new_comment)

    db.session.commit()
