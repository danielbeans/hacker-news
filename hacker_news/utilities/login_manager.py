"""
Utilities for managing User login and sessions

Methods:
    init_oauth(oauth):
    load_user(id):
    unauthorized():
    session_login(token):
    admin_required(func):
    check_member_role(email):

Variables:
    login_manager
    oauth
"""

import os
from functools import wraps
from urllib.parse import urlparse
from uuid import uuid4
from authlib.integrations.flask_client import OAuth
from flask import redirect, url_for, request, session, current_app
from flask_login import LoginManager, login_user, current_user
from ..db import db, User

login_manager = LoginManager()
oauth = OAuth()


def init_oauth(oauth_handler):
    """
    Initialize OAuth object with variables from .env

    Parameters:
        oauth (OAuth): OAuth object to initialize
    """
    auth0_client_id = os.getenv("AUTH0_CLIENT_ID")
    auth0_client_secret = os.getenv("AUTH0_CLIENT_SECRET")
    auth0_domain = os.getenv("AUTH0_DOMAIN")

    oauth_handler.register(
        "auth0",
        client_id=auth0_client_id,
        client_secret=auth0_client_secret,
        client_kwargs={
            "scope": "openid profile email",
        },
        server_metadata_url=f"https://{auth0_domain}/.well-known/openid-configuration",
    )


@login_manager.user_loader
def load_user(user_id):
    """
    Callback route to reload user from userID in session. Used by Flask_login

    Parameters:
        id (string): User ID

    Returns:
        user (User): A User object
    """
    return User.find_item(user_id)


@login_manager.unauthorized_handler
def unauthorized():
    """
    Route called when a User isn't logged in

    Returns:
        response (Response): A redirect Response object
    """
    url_redirect = None
    if request.referrer:
        url_redirect = request.referrer
        # Remove parameters to prevent duplicate login_required
        url_redirect = url_redirect.replace("?" + urlparse(request.referrer).query, "")
        url_redirect += "?login_required=true"

    return redirect(url_redirect or url_for("home.index", login_required="true"))


def session_login(token):
    """
    Logic to login user with query to database

    Parameters:
        token (Object): An object holding User information and tokens

    Returns:
        login_user (bool): Whether or not a user is successfully logged in
    """
    user_info = token["userinfo"]

    user = db.session.scalars(
        db.select(User).filter_by(email=user_info["email"])
    ).one_or_none()

    if not user:
        user_nickname = (
            user_info["given_name"]
            if "given_name" in user_info
            else user_info["nickname"]
        )
        user = User(
            id=str(uuid4()),
            email=user_info["email"],
            name=user_info["name"],
            nickname=user_nickname,
        )
        db.session.add(user)

    # Assign proper role based on config file
    user = db.session.merge(User(id=user.id, role=check_member_role(user.email)))

    db.session.add(user)
    db.session.commit()

    session["is_authenticated"] = True
    return login_user(user)


def admin_required(func):
    """
    Decorate a view to ensure the current user has an admin role

    Parameters:
        func (function): The view function to decorate
    """

    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.role == "admin":
            url_redirect = None
            if request.referrer:
                url_redirect = request.referrer
                # Remove parameters to prevent duplicate login_required
                url_redirect = url_redirect.replace(
                    "?" + urlparse(request.referrer).query, ""
                )
                url_redirect += "?admin_required=true"

            return redirect(
                url_redirect or url_for("home.index", admin_required="true")
            )

        return func(*args, **kwargs)

    return decorated_view


def check_member_role(email):
    """
    Check config.json to see whhich User has the admin role

    Parameters:
        email (string): User email to check against config.json

    Returns:
        A string of what role the email is assigned
    """
    if admin_list := current_app.config.get("ADMIN_LIST"):
        if email in admin_list:
            return "admin"
    return "member"
