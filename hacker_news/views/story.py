"""
Defines the routes for the profile page

Methods:
    story_exists(func)
    set_current_user(endpoint, values)
    index()
    like()
    edit()
    update()
    delete()

Variables:
    story
"""

from urllib.parse import urlparse
from functools import wraps
from flask import Blueprint, render_template, g, redirect, url_for, request
from flask_login import current_user, login_required
from .home import calculate_publish_time
from ..utilities import (
    query_story,
    query_comments,
    admin_required,
    edit_story,
    delete_story,
)

story = Blueprint("story", __name__, url_prefix="/story/<id>")


def story_exists(func):
    """
    Decorate a view to ensure the story exists

    Parameters:
        func (function): The view function to decorate
    """

    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not query_story(kwargs.get("id", "")):
            url_redirect = None
            if request.referrer:
                url_redirect = request.referrer
                # Remove parameters to prevent duplicate no_story
                url_redirect = url_redirect.replace(
                    "?" + urlparse(request.referrer).query, ""
                )
                url_redirect += "?no_story=true"

            return redirect(url_redirect or url_for("home.index", no_story="true"))
        return func(*args, **kwargs)

    return decorated_view


@story.url_value_preprocessor
def set_current_user(endpoint, values):
    """
    Sets variables before route is called

    Parameters:
        endpoint: Endpoint
        values (dict): All the values route is called with
    """
    g.current_user = current_user
    if story := query_story(values.get("id", "")):
        g.story = query_story(story.id)
        g.comments = query_comments(story.id)
        g.publish_time = calculate_publish_time(story.time)
        g.like_statuses = None
        if current_user.is_authenticated:
            liked_story = current_user.has_liked_story(story.id)
            if liked_story:
                g.like_status = liked_story.type
            else:
                g.like_statuses = None
        else:
            g.like_statuses = None


@story.route("/")
@story_exists
def index(id):
    """
    Index route for viewing the story page

    Parameters:
        id (string): Story ID

    Returns:
        Renders story.html
    """
    return render_template("story.html")


@story.route("/<type>/<action>")
@story_exists
@login_required
def like(id, type, action):
    """
    Route for liking/disliking stories

    Parameters:
        id (string): Story ID of story to update
        type (string): Like or dislike
        action (string): Add or remove a like or dislike

    Returns:
        A JSON describing the type and action just queried
    """
    action = action.lower()
    type = type.lower()

    if action == "add":
        current_user.like_story(story_id=id, action=action, type=type)
    elif action == "remove":
        current_user.like_story(story_id=id, action=action, type=type)

    return {"type": type, "action": action, "status": "success"}


@story.route("/edit")
@story_exists
@login_required
@admin_required
def edit(id):
    """
    Route for editing a story

    Parameters:
        id (string): Story ID

    Returns:
        Renders edit-story.html
    """
    return render_template("edit-story.html")


@story.route("/update", methods=["POST", "GET"])
@story_exists
@login_required
@admin_required
def update(id):
    """
    Route for updating a story's information using form data

    Parameters:
        id (string): Story ID for story to update

    Returns:
        Redirects to story edit route
    """
    if request.method == "POST":
        keywords = request.form.get("keywords")
        edit_story(id, keywords=keywords)

    return redirect(url_for("story.edit", id=id))


@story.route("/delete")
@story_exists
@login_required
@admin_required
def delete(id):
    """
    Route for deleting a story

    Parameters:
        id (string): Story ID for story to delete

    Returns:
        Redirects to home index
    """
    delete_story(id)
    return redirect(url_for("home.index"))
