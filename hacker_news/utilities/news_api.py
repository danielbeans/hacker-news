"""
Utilites for interacting with the Hacker News API and the database for all
Hacker News data.

Methods:
    create_data()
    update_data()
    create_data_command(update)
    add_create_data_command(app)
    query_top_stories(count)
    query_story(id)
    query_comments(story_id)
    query_liked_stories()
    query_disliked_stories()
    query_story_association_all(type)
    query_story_association_by_id(story_id, user_id)
    edit_story(id, **kwargs)
    delete_story(id)
    get_top_stories(count)
    get_stories(url, count)
    get_comments(story)
    async_fetch_item(client_session, item_id)
    insert_stories_db(stories)
    insert_comments_db(comments)

Variables:
    MAX_STORY_COUNT
    UPDATE_DB
    UPDATE_COMMENTS
    IDS_QUERIED
"""

from os.path import exists
from time import time
import asyncio
import aiohttp
import click
import requests
from flask.cli import with_appcontext
from keybert import KeyBERT
from ..db import (
    db,
    Story,
    Comment,
    StoryAssociation,
)

MAX_STORY_COUNT = 20
# Enables or disables API query and database insertion of duplicate items
UPDATE_DB = False
UPDATE_COMMENTS = False
IDS_QUERIED = 0


async def create_data():
    """
    Populates database with story and comment data, used in
    'create-data' flask command
    """
    # Insert Stories into database
    stories = await get_top_stories(count=MAX_STORY_COUNT)
    insert_stories_db(stories=stories)

    # Insert Comments into database
    # toggle = WebsiteSetting.find_item("toggle_comments")
    if UPDATE_COMMENTS:
        comments = [
            await get_comments(story) for story in stories
        ]  # List of lists of dicts
        insert_comments_db(comments=comments)


async def update_data(comments=False):
    """
    Updates database story data, used in 'get_new_api_data' APScheduler task.
    Calls create_data()

    Parameters:
        comments (bool): Determines whether to query for comments
    """
    global UPDATE_DB, UPDATE_COMMENTS
    UPDATE_DB = True
    UPDATE_COMMENTS = comments
    await create_data()


# Takes in flag '--update' to update the items already in the database, if any
@click.command("create-data")
@click.option("--update", is_flag=True)
@with_appcontext
def create_data_command(update: bool):
    """
    Function called from CLI command "Flask create-data"

    Parameters:
        update (bool): Determines whether to update entries in the database
    """
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


def add_create_data_command(app):
    """
    Called in app.py to add command to flask

    Parameters:
        app: Flask app object
    """
    app.cli.add_command(create_data_command)


###################################################
#                                                 #
# 'query_*' functions access database.db for data #
#                                                 #
###################################################


def query_top_stories(count=1):
    """
    Queries the database for the top stories, determined by order number

    Parameters:
        count (int): The amount of stories to pull

    Returns:
        stories (list): A list of Story objects
    """
    return db.session.scalars(
        db.select(Story).order_by(Story.order_num.desc()).limit(count)
    ).all()


def query_story(story_id):
    """
    Query the database for a story

    Parameters:
        story_id (string): ID number of the story to pull from the database

    Returns:
        story (Story): A Story object or None
    """
    story = db.session.scalars(db.select(Story).filter_by(id=story_id)).one_or_none()
    return story


def query_comments(story_id):
    """
    Query the databse for comments from a story

    Parameters:
        story_id (string): ID number of the story to get comments for

    Returns:
        comments (list): A list of Comment objects
    """
    comments = db.session.scalars(db.select(Comment).filter_by(story_id=story_id)).all()
    return comments


def query_liked_stories():
    """
    Query the database for all stories that are liked

    Returns:
        liked_stories (list): A list of Story objects
    """
    liked_stories = query_story_association_all(association_type="like")
    liked_stories = [query_story(story.story_id) for story in liked_stories]
    return liked_stories


def query_disliked_stories():
    """
    Query the database for all stories that are disliked

    Returns:
        disliked_stories (list): A list of Story objects
    """
    disliked_stories = query_story_association_all(association_type="dislike")
    disliked_stories = [query_story(story.story_id) for story in disliked_stories]
    return disliked_stories


def query_story_association_all(association_type):
    """
    Query the database for all story associations. These define User and Story
    many to many relationships

    Parameters:
        type (string): Type of StoryAssociation to get, like or dislike

    Returns:
        story_associations (list): A list of StoryAssocitation objects
    """
    story_associations = db.session.scalars(
        db.select(StoryAssociation).filter_by(type=association_type)
    ).all()
    return story_associations


def query_story_association_by_id(story_id=None, user_id=None):
    """
    Query the database for a story association by id. These define User
    and Story many to many relationships

    Parameters:
        story_id (string): Story ID to match story association with. Optional
        user_id (string): User ID to match story association with. Optional

    Returns:
        story_association : A StoryAssocitation object or None
    """
    if story_id:
        story_association = db.session.scalars(
            db.select(StoryAssociation).filter_by(story_id=story_id)
        ).all()
    elif user_id:
        story_association = db.session.scalars(
            db.select(StoryAssociation).filter_by(user_id=user_id)
        ).all()
    else:
        story_association = None
    return story_association


def edit_story(story_id, **kwargs):
    """
    Edit a story in the database

    Parameters:
        story_id (string): Story ID of the story to edit
        **kwargs (dict): A dict of which fields of a story to edit
    """
    story = query_story(story_id)
    story = db.session.merge(
        Story(id=story_id, keywords=kwargs.get("keywords", story.keywords))
    )
    db.session.add(story)
    db.session.commit()


def delete_story(story_id):
    """
    Delete a story from the database

    Parameters:
        story_id (string): Story ID of the story to delete
    """
    # If a user has liked/disliked story
    if found_story_assoc := StoryAssociation.find_item_story_id(story_id):
        db.session.delete(found_story_assoc)
    db.session.delete(query_story(story_id))
    db.session.commit()


#####################################################
#                                                   #
# 'get_*' functions access Hacker News API for data #
#                                                   #
#####################################################


async def get_top_stories(count):
    """
    Get top stories from Hacker News API

    Parameters:
        count (int): Number of stories to get

    Returns:
        top_stories (list): A list of dictionaries with story information
    """
    return await get_stories(
        url="https://hacker-news.firebaseio.com/v0/topstories.json", count=count
    )


async def get_stories(url, count):
    """
    Get stories from Hacker News API asynchronously

    Parameters:
        url (string): The url to query Hacker News API with
        count (int): Number of stories to get

    Returns:
        stories (list): A list of dictionaries with story information
    """
    tasks, stories = [], []
    # 500 is the max items the Hacker News API returns
    count = MAX_STORY_COUNT if count > MAX_STORY_COUNT else count

    # Fetch id's from Hacker News API
    story_ids: list = requests.get(url, timeout=10).json()

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
    """
    Get comments from Hacker News API asynchronously

    Parameters:
        story (dict): A dictionary representing a story

    Returns:
        all_comments (list): A list of dictionaries with comment information
    """
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


async def async_fetch_item(client_session, item_id):
    """
    Get an item from Hacker News API asynchronously

    Parameters:
        client_session (ClientSession): A ClientSession aiohttp object for making async requests
        item_id (string): Item ID to query

    Returns:
        response (dict): A dictionary with the items information
    """
    global IDS_QUERIED
    IDS_QUERIED += 1
    res = await client_session.get(
        f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
    )
    return await res.json()


def insert_stories_db(stories):
    """
    Insert stories into the database

    Parameters:
        stories (list): A list of dictionaries with story information
    """
    # Guarantees order of stories is correct
    num_story_rows = db.session.query(Story).count()
    kw_model = KeyBERT()
    for num, story in enumerate(stories[::-1]):
        found_story = Story.find_item(story["id"])
        if not found_story:
            keywords_list = kw_model.extract_keywords(story.get("title", ""))
            keywords = " ".join([keyword[0] for keyword in keywords_list])
            found_story = Story(
                id=story.get("id"),
                title=story.get("title"),
                score=story.get("score"),
                time=story.get("time"),
                author=story.get("by"),
                url=story.get("url", ""),
                order_num=num + num_story_rows,
                num_comments=story.get("descendants", 0),
                keywords=keywords,
            )
        elif found_story and UPDATE_DB:
            found_story = db.session.merge(
                Story(
                    id=story.get("id"),
                    score=story.get("score"),
                    num_comments=story.get("descendants", 0),
                )
            )
        db.session.add(found_story)
    db.session.commit()


def insert_comments_db(comments):
    """
    Insert comments into the database

    Parameters:
        comments (list): A list of dictionaries with comment information
    """

    def insert_child_comments(parent_comment, parent_comment_object):
        for comment in parent_comment["kids"]:
            # Doesn't update comment information
            # (SQLAlchemy's merge function is giving issues)
            found_comment = Comment.find_item(comment["id"])
            if not comment.get("dead", False) and not found_comment:
                comment_object = Comment(
                    id=comment.get("id"),
                    time=comment.get("time"),
                    author=comment.get("by"),
                    text=comment.get("text"),
                    type="child",
                    parent_comment=parent_comment_object,
                )
                db.session.add(comment_object)

                if comment.get("kids"):
                    insert_child_comments(
                        parent_comment=comment,
                        parent_comment_object=comment_object,
                    )

    for root_comments in comments:
        for root_comment in root_comments:
            # Doesn't update comment information
            # (SQLAlchemy's merge function is giving issues)
            found_comment = Comment.find_item(root_comment["id"])
            if not root_comment.get("dead", False) and not found_comment:
                comment_object = Comment(
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
                        parent_comment_object=comment_object,
                    )
                db.session.add(comment_object)
    db.session.commit()
