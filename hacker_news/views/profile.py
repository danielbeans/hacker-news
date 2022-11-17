from flask import Blueprint, render_template, redirect, request, url_for, g
from flask_login import login_required, current_user


profile = Blueprint("profile", __name__, url_prefix=f"/profile/<username>")


@profile.url_value_preprocessor
def set_current_user(endpoint, values):
    g.current_user = current_user


@profile.route("/")
@login_required
def index(username):
    if username.lower() != g.current_user.nickname.lower():
        return redirect(url_for("home.index"))
    return render_template("profile.html")
