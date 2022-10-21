from flask import Flask

from .db import db
from . import views
from .utilities import login_manager, add_create_data_command
from dotenv import load_dotenv
import os
from .tasks import scheduler


def create_app():
    basedir = os.path.abspath(os.path.dirname(__file__))  # ./hacker-news-project
    database_path = os.path.join(basedir, "db", "database.db")

    app = Flask(__name__)
    app.secret_key = os.getenv("APP_SECRET_KEY")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{database_path}"

    # Load .env
    load_dotenv()

    # Load Flask-Login
    login_manager.init_app(app)

    # Start scheduler for running tasks (under './tasks')
    scheduler.init_app(app)
    scheduler.start()

    # Initilize Flask app to use database with SQLAlchemy
    db.init_app(app)
    with app.app_context():
        db.create_all()

    # Add command 'create-data to add/update data from Hacker News API into the database
    add_create_data_command(app)

    # Register frontend templates
    app.register_blueprint(views.admin)
    app.register_blueprint(views.home)
    app.register_blueprint(views.login)
    app.register_blueprint(views.profile)

    return app
