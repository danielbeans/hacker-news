from flask import Blueprint, render_template

signup = Blueprint("signup", __name__, url_prefix="/signup")


@signup.route("/")
def index():
    return render_template("signup.html")
