from flask import Blueprint, render_template, redirect, url_for, session, g
import os
from urllib.parse import quote_plus, urlencode
from flask_login import logout_user, current_user, login_required
from ..utilities import query_top_stories, query_new_stories, update_data
from time import time
from datetime import timedelta
import asyncio

home = Blueprint("home", __name__)

auth0_client_id = os.getenv("AUTH0_CLIENT_ID")
auth0_domain = os.getenv("AUTH0_DOMAIN")


def zip_stories(stories):
    """
    Calculates a story order number and publish time and zips them with their story
    Arguments:
        stories: An list of TopStory or NewStory objects
    Returns:
        A zip object with tuples (order number, story, publish time)
    """
    publish_times = [calculate_publish_time(story.time) for story in stories]
    return zip(range(1, len(stories) + 1), stories, publish_times)


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

    numbered_top_stories = zip_stories(stories=query_top_stories(num_stories))
    numbered_new_stories = zip_stories(stories=query_new_stories(num_stories))
    return render_template(
        "home.html",
        top_stories=numbered_top_stories,
        new_stories=numbered_new_stories,
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
