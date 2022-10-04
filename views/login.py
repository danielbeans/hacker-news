from flask import Blueprint, render_template

login = Blueprint("login", __name__, url_prefix="/login")


@login.route("/")
def index():
    return render_template("login.html")
