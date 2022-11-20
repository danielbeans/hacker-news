"""
Defines the routes for the profile page

Methods:
    zip_stories(stories, type)
    set_current_user(endpoint, values)
    index()

Variables:
    profile
"""

from flask import Blueprint, render_template, redirect, url_for, g
from flask_login import login_required, current_user
from ..utilities import (
    query_story_association_by_id,
    query_liked_stories,
    query_disliked_stories,
)


profile = Blueprint("profile", __name__, url_prefix="/profile/<username>")


# * Similar functionality in admin.py, home.py
def zip_stories(stories, type):
    """
    Removes duplicate stories, calculates which stories the user liked/disliked

    Arguments:
        stories (list): An list of Story objects
        type (string): Type of StoryAssociation to search for

    Returns:
        A list of stories
    """
    stories = [*set(stories)]  # Removes duplicates
    found_stories = []
    # Kinda inefficient
    for story in stories:
        if story_associations := query_story_association_by_id(story_id=story.id):
            for story_assoc in story_associations:
                if story_assoc.type == type and story_assoc.user_id == current_user.id:
                    found_stories.append(story)
    return found_stories


@profile.url_value_preprocessor
def set_current_user(endpoint, values):
    """
    Sets variables before route is called

    Parameters:
        endpoint: Endpoint
        values (dict): All the values route is called with
    """
    g.current_user = current_user


@profile.route("/")
@login_required
def index(username):
    """
    Index route for viewing the profile page

    Parameters:
        username (string): Username of User currently logged in

    Returns:
        Renders profile.html
    """
    if username.lower() != g.current_user.nickname.lower():
        return redirect(url_for("home.index"))

    liked_stories = zip_stories(query_liked_stories(), type="like")
    disliked_stories = zip_stories(query_disliked_stories(), type="dislike")
    return render_template(
        "profile.html", liked_stories=liked_stories, disliked_stories=disliked_stories
    )
