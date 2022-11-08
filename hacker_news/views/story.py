from flask import Blueprint, render_template, g
from flask_login import current_user, login_required

from hacker_news.utilities.news_api import query_comments
from ..utilities import query_story
from .home import calculate_publish_time

story = Blueprint("story", __name__, url_prefix="/story/<id>")


@story.url_value_preprocessor
def set_current_user(endpoint, values):
    g.current_user = current_user


@story.route("/")
def index(id):
    story = query_story(id)
    comments = query_comments(id)
    publish_time = calculate_publish_time(story.time)
    return render_template(
        "story.html", story=story, comments=comments, publish_time=publish_time
    )


@story.route("/<type>/<action>")
@login_required
def like(id, type, action):
    action = action.lower()
    type = type.lower()

    if action == "add":
        current_user.like_story(story_id=id, action=action, type=type)
    elif action == "remove":
        current_user.like_story(story_id=id, action=action, type=type)

    return {"type": type, "action": action, "status": "success"}
