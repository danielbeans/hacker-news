from operator import ge
from flask import Blueprint, current_app, render_template, redirect, session, url_for
from authlib.integrations.flask_client import OAuth
import os
from ..utilities import session_login

login = Blueprint("login", __name__, url_prefix="/login")

oauth = OAuth(current_app)
auth0_client_id = os.getenv("AUTH0_CLIENT_ID")
auth0_client_secret = os.getenv("AUTH0_CLIENT_SECRET")
auth0_domain = os.getenv("AUTH0_DOMAIN")

oauth.register(
    "auth0",
    client_id=auth0_client_id,
    client_secret=auth0_client_secret,
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f"https://{auth0_domain}/.well-known/openid-configuration",
)


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
