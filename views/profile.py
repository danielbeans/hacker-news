from flask import Blueprint, render_template, redirect, request, url_for
from flask_login import login_required, current_user


profile = Blueprint("profile", __name__, url_prefix=f"/profile/<username>")


@profile.route("/")
@login_required
def index(username):
    if username.lower() != current_user.nickname.lower():
        return redirect(url_for(request.referrer or "home.index"))
    return render_template("profile.html", profile=username)
