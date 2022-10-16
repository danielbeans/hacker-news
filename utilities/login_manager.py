from flask_login import LoginManager, UserMixin, login_user
from ..db import query_db
from uuid import uuid4
from flask import session

login_manager = LoginManager()

# Callback route to reload user from userID in session
@login_manager.user_loader
def load_user(id):
    return UserLogin.get(id)


# Logic to login user with query to database
def session_login(token):
    user_info = token["userinfo"]

    user = query_db(
        "SELECT * FROM user WHERE email = ?", (user_info["email"],), one=True
    )

    if not user:
        user_nickname = (
            user_info["given_name"]
            if user_info["given_name"]
            else user_info["nickname"]
        )
        query_db(
            "INSERT INTO user (id, email, name, nickname) VALUES (?, ?, ?, ?)",
            (str(uuid4()), user_info["email"], user_info["name"], user_nickname),
        )
        user = query_db(
            "SELECT * FROM user WHERE email = ?", (user_info["email"],), one=True
        )

    session["is_authenticated"] = True
    return login_user(UserLogin(user))


class UserLogin(UserMixin):
    def __init__(self, user):
        self.id = user["id"]
        self.name = user["name"]
        self.nickname = user["nickname"]
        self.email = user["email"]

    def __repr__(self):
        return "%s %s %s" % (self.id, self.name, self.email)

    def get(id):
        return UserLogin(query_db("SELECT * FROM user WHERE id = ?", (id,), one=True))
