from flask import Blueprint, current_app, render_template, redirect, session, url_for
from authlib.integrations.flask_client import OAuth
from ..utilities import session_login, oauth

login = Blueprint("login", __name__, url_prefix="/login")


@login.route("/")
def index():
    # Redirect to auth0 for auth then go to login callback route
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("login.callback", _external=True)
    )


@login.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    if session_login(token):
        return redirect(url_for("home.index"))
    return redirect(url_for("login.index"))
