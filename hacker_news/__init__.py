"""
Create Flask application to be used on development or production WSGI servers.
Initializes config, login manager, OAuth, the database, registers commands,
and blueprints.

Methods:
    create_app() -> Flask object
"""

import os
import json
from flask import Flask
from dotenv import load_dotenv
from .db import db
from .tasks import scheduler
from .utilities import login_manager, add_create_data_command, oauth, init_oauth
from . import views


def create_app():
    """
    Creates Flask application and initializes libraries.

    Returns:
        app: Flask object
    """
    # Load .env when in production (Flask CLI tool isn't used)
    load_dotenv()

    # Create Flask application and add config from .env and config.json
    app = Flask(__name__)
    app.config.from_file("../config.json", load=json.load, silent=True)
    app.secret_key = os.getenv("APP_SECRET_KEY")

    # Load Flask-Login
    login_manager.init_app(app)

    # Initialize OAuth client
    oauth.init_app(app)
    init_oauth(oauth)

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
    app.register_blueprint(views.story)

    return app
