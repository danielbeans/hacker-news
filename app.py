from flask import Flask
import api.db as db
import api
import views


def create_app():
    app = Flask(__name__)

    db.init_app(app)

    # Register frontend templates
    app.register_blueprint(views.admin)
    app.register_blueprint(views.home)
    app.register_blueprint(views.login)
    app.register_blueprint(views.profile)
    app.register_blueprint(views.signup)

    # Register API Blueprints
    app.register_blueprint(api.api)

    return app
