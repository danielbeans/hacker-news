from flask import Flask
from .db import add_init_db_command
from . import views
from .utilities import login_manager, add_create_data_command
from dotenv import load_dotenv
import os


def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv("APP_SECRET_KEY")

    # Load .env
    load_dotenv()

    # Load Flask-Login
    login_manager.init_app(app)

    # Add command 'init-db' to create SQLite3 database
    add_init_db_command(app)

    # Add command 'create-data to add/update data from Hacker News API into the database
    add_create_data_command(app)

    # Register frontend templates
    app.register_blueprint(views.admin)
    app.register_blueprint(views.home)
    app.register_blueprint(views.login)
    app.register_blueprint(views.profile)

    return app
