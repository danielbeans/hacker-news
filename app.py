from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("home.html")


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/signup")
def signup():
    return render_template("signup.html")


@app.route("/profile")
def profile():
    return render_template("profile.html")


@app.route("/admin")
def admin():
    return render_template("admin.html")
