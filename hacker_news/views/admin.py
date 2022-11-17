from flask import Blueprint, render_template, g
from flask_login import login_required, current_user
from ..utilities import (
    admin_required,
    query_liked_stories,
    query_disliked_stories,
    query_story_association_by_id,
    User,
)

admin = Blueprint("admin", __name__, url_prefix="/admin")

# * Similar functionality in profile.py, home.py
def zip_stories(stories, type):
    """
    Removes duplicate stories, calculates which users liked/disliked a story and zips them with their story
    Arguments:
        stories: An list of Story objects
        type: Type of StoryAssociation to search for
    Returns:
        A zip object with tuples (story, [list of users])
    """
    stories = [*set(stories)]  # Removes duplicates
    total_users = []
    for story in stories:
        if story_associations := query_story_association_by_id(story_id=story.id):
            users = []
            for story_assoc in story_associations:
                if story_assoc.type == type:
                    users.append(User.find_item(story_assoc.user_id))
            total_users.append(users)

    return zip(stories, total_users)


@admin.url_value_preprocessor
def set_current_user(endpoint, values):
    g.current_user = current_user


@admin.route("/")
@login_required
@admin_required
def index():
    liked_stories = zip_stories(query_liked_stories(), type="like")
    disliked_stories = zip_stories(query_disliked_stories(), type="dislike")
    return render_template(
        "admin.html", liked_stories=liked_stories, disliked_stories=disliked_stories
    )
