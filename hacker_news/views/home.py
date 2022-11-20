"""
Defines the routes for the home page

Methods:
    zip_stories(stories, type)
    calculate_publish_time(timestamp)
    set_current_user(endpoint, values)
    index()
    update()
    update_comments()
    logout()

Variables:
    home
"""

import asyncio
import os
from time import time
from urllib.parse import quote_plus, urlencode
from flask import Blueprint, render_template, redirect, url_for, session, g
from flask_login import logout_user, current_user, login_required
from ..utilities import query_top_stories, update_data, admin_required

home = Blueprint("home", __name__)

# * Similar functionality in admin.py, profile.py
def zip_stories(stories):
    """
    Calculates a story order number, publish time, and like/dislike
    status and zips them with their story

    Parameters:
        stories (list): An list of Story objects

    Returns:
        A zip object with tuples (order number, story, publish time)
    """
    publish_times, like_statuses = [], []
    for story in stories:
        publish_times.append(calculate_publish_time(story.time))
        if current_user.is_authenticated:
            liked_story = current_user.has_liked_story(story.id)
            if liked_story:
                like_statuses.append(liked_story.type)
            else:
                like_statuses.append(None)
        else:
            like_statuses.append(None)

    return zip(range(1, len(stories) + 1), stories, publish_times, like_statuses)


def calculate_publish_time(timestamp):
    """
    Calculate how much time has past since story was published

    Parameters:
        timestamp (string): Unix timestamp used to calculate publish time

    Returns:
        An integer of the time in minutes since story was published
    """
    return int((time() - timestamp) // 60)


@home.url_value_preprocessor
def set_current_user(endpoint, values):
    """
    Sets variables before route is called

    Parameters:
        endpoint: Endpoint
        values (dict): All the values route is called with
    """
    g.current_user = current_user


@home.route("/")
def index():
    """
    Index route that shows homepage with the top stories

    Returns:
        Returns home.html
    """
    num_stories = 20

    numbered_stories = zip_stories(stories=query_top_stories(num_stories))
    return render_template(
        "home.html",
        stories=numbered_stories,
    )


@home.route("/update")
def update():
    """
    Route that updates the database with Hacker News data

    Returns:
        Redirects to the index route
    """
    asyncio.run(update_data())
    return redirect(url_for(endpoint="home.index"))


@home.route("/update/comments")
@admin_required
@login_required
def update_comments():
    """
    Route that gets the comments for each story in the database from Hacker
    News API

    Returns:
        Returns JSON of the time it took to update database with comments
    """
    start = time()
    asyncio.run(update_data(comments=True))
    return {"time_taken": f"{round(time() - start, 3)}"}


@home.route("/logout")
@login_required
def logout():
    """
    Route that logs out the User

    Returns:
        Redirects to auth0 to logout user
    """
    logout_user()
    session.pop("is_authenticated")
    auth0_client_id = os.getenv("AUTH0_CLIENT_ID")
    auth0_domain = os.getenv("AUTH0_DOMAIN")
    return redirect(
        "https://"
        + auth0_domain
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("home.index", _external=True),
                "client_id": auth0_client_id,
            },
            quote_via=quote_plus,
        )
    )
