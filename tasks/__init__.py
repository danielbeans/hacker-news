from flask_apscheduler import APScheduler
from time import time
import asyncio

from ..utilities import update_data

scheduler = APScheduler()


@scheduler.task("interval", id="get_new_api_data", seconds=300, misfire_grace_time=900)
def get_new_api_data():
    with scheduler.app.app_context():
        start = time()
        asyncio.run(update_data())
        print(f"Updated data from API in {round(time() - start, 3)} seconds")
