import requests

# Populates database with post and comment data
def init_api_data():
    pass


def get_top_stories(num=1):
    pass


def query_top_stories(num):
    # 500 is the max items the news api returns
    if num > 500:
        num = 500
    top_stories = {}
    top_story_ids: list = requests.get(
        "https://hacker-news.firebaseio.com/v0/topstories.json"
    ).json()

    for top_story_id in top_story_ids[:num]:
        top_story = requests.get(
            f"https://hacker-news.firebaseio.com/v0/item/{top_story_id}.json"
        ).json()

    return top_stories
