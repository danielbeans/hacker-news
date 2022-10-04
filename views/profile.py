from flask import Blueprint, render_template

profile = Blueprint("profile", __name__, url_prefix="/<username>")


@profile.route("/")
def index(username):
    print(f"hi, {username}")
    return render_template("profile.html", profile=username)
