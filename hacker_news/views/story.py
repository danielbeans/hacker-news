from flask import Blueprint, render_template, g
from flask_login import current_user

from hacker_news.utilities.news_api import query_comments
from ..utilities import query_story
from .home import calculate_publish_time

story = Blueprint("story", __name__, url_prefix="/story")


@story.url_value_preprocessor
def set_current_user(endpoint, values):
    g.current_user = current_user


@story.route("/<id>")
def index(id):
    story = query_story(id)
    comments = query_comments(id)
    publish_time = calculate_publish_time(story.time)
    return render_template(
        "story.html", story=story, comments=comments, publish_time=publish_time
    )
