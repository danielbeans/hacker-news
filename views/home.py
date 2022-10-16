from flask import Blueprint, render_template, redirect, url_for, session, g
import os
from urllib.parse import quote_plus, urlencode
from flask_login import logout_user, current_user, login_required
from ..utilities import query_top_stories


home = Blueprint("home", __name__)

auth0_client_id = os.getenv("AUTH0_CLIENT_ID")
auth0_domain = os.getenv("AUTH0_DOMAIN")


@home.url_value_preprocessor
def set_current_user(endpoint, values):
    g.current_user = current_user


@home.route("/")
def index():
    num_stories = 30
    numbered_top_stories = zip(
        range(1, num_stories + 1), query_top_stories(num_stories)
    )
    return render_template("home.html", top_stories=numbered_top_stories)


@home.route("/logout")
@login_required
def logout():
    logout_user()
    session.pop("is_authenticated")
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
