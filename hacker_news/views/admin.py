from flask import Blueprint, render_template, g
from flask_login import login_required, current_user
from ..utilities import admin_required

admin = Blueprint("admin", __name__, url_prefix="/admin")


@admin.url_value_preprocessor
def set_current_user(endpoint, values):
    g.current_user = current_user


@admin.route("/")
@admin_required
@login_required
def index():
    return render_template("admin.html")
