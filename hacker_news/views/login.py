"""
Defines the routes for the login functionality

Methods:
    index()
    callback()

Variables:
    login
"""

from flask import Blueprint, redirect, url_for
from ..utilities import session_login, oauth

login = Blueprint("login", __name__, url_prefix="/login")


@login.route("/")
def index():
    """
    Redirects to auth0 for auth, then goes to login callback route

    Returns:
        Redirects to auth0 for login
    """
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("login.callback", _external=True)
    )


@login.route("/callback", methods=["GET", "POST"])
def callback():
    """
    Callback that auth0 references after successful or unsuccessful login

    Returns:
        Redirects to home if logged in, else back to login index
    """
    token = oauth.auth0.authorize_access_token()
    if session_login(token):
        return redirect(url_for("home.index"))
    return redirect(url_for("login.index"))
