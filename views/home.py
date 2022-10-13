from flask import Blueprint, render_template, redirect, url_for
import os
from urllib.parse import quote_plus, urlencode
from flask_login import logout_user, current_user, login_required
from ..utilities import get_top_stories


home = Blueprint("home", __name__)

auth0_client_id = os.getenv("AUTH0_CLIENT_ID")
auth0_domain = os.getenv("AUTH0_DOMAIN")


@home.route("/")
def index():
    # If user token from auth0 is in session object (essentially a dict)
    if current_user.is_authenticated:
        for story in get_top_stories(2):
            for key in story.keys():
                print(f"{key}: {story[key]}")
        return render_template("home.html")
    return render_template("login.html")


@home.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(
        "https://"
        + auth0_domain
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("home.index", _external=True),
                "client_id": auth0_client_id,
            },
            quote_via=quote_plus,
        )
    )
