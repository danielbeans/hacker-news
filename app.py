from flask import Flask
from .db import init_app
from . import views
from .utilities import login_manager, init_api_data
from dotenv import load_dotenv
import os, time


def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv("APP_SECRET_KEY")

    # Load .env
    load_dotenv()

    # Load Flask-Login
    login_manager.init_app(app)

    # Initilize SQLite3 database
    init_app(app)

    """
    Populate database with Hacker News data
    * Will take a couple minutes if database is empty
    """
    with app.app_context():
        start = time.time()
        print(" ** Adding Hacker News data **")
        init_api_data()
        print(f" * Done in {time.time() - start} *")

    # Register frontend templates
    app.register_blueprint(views.admin)
    app.register_blueprint(views.home)
    app.register_blueprint(views.login)
    app.register_blueprint(views.profile)

    return app
