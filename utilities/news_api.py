import requests
from ..db import query_db

MAX_STORY_COUNT = 500

# Populates database with post and comment data, used in app.py
def init_api_data():
    stories_dict = {
        "top_stories": query_stories("top", 500),
        "new_stories": query_stories("new", 500),
    }
    for stories_type, stories in stories_dict.items():
        for story in stories:
            query_db(
                f"INSERT INTO {stories_type} (id, title, score, time, author, url) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    story["id"],
                    story["title"],
                    story["score"],
                    story["time"],
                    story["by"],
                    story["url"] if "url" in story else "",
                ),
            )


def get_top_stories(num=1):
    return query_db(f"SELECT * FROM top_stories LIMIT {num}")


def query_stories(type, num):
    # 500 is the max items the news api returns
    if num > MAX_STORY_COUNT:
        num = MAX_STORY_COUNT

    if type == "top":
        story_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        story_db_table = "top_stories"
    elif type == "new":
        story_url = "https://hacker-news.firebaseio.com/v0/newstories.json"
        story_db_table = "new_stories"

    stories = []
    story_ids: list = requests.get(story_url).json()

    for story_id in story_ids[:num]:
        if not query_db(f"SELECT * FROM {story_db_table} WHERE id = ?", (story_id,)):
            stories.append(
                requests.get(
                    f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                ).json()
            )

    return stories
