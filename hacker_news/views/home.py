from flask import Blueprint, render_template, redirect, url_for, session, g, request
import os
from urllib.parse import quote_plus, urlencode
from flask_login import logout_user, current_user, login_required
from ..utilities import query_top_stories, update_data, oauth
from time import time
from datetime import timedelta
import asyncio

home = Blueprint("home", __name__)


def zip_stories(stories):
    """
    Calculates a story order number, publish time, and like/dislike status and zips them with their story
    Arguments:
        stories: An list of TopStory or NewStory objects
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
    Arguments:
        timestamp: Unix timestamp used to calculate publish time
    Returns:
        The time in minutes since story was published
    """
    return int((time() - timestamp) // 60)


@home.url_value_preprocessor
def set_current_user(endpoint, values):
    g.current_user = current_user


@home.route("/")
def index():
    num_stories = 30

    numbered_stories = zip_stories(stories=query_top_stories(num_stories))
    return render_template(
        "home.html",
        stories=numbered_stories,
    )


@home.route("/update")
def update():
    asyncio.run(update_data())
    return redirect(url_for(endpoint="home.index"))


@home.route("/logout")
@login_required
def logout():
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
