from flask_login import LoginManager, UserMixin, login_user
from uuid import uuid4
from flask import session
from ..db import db, User

login_manager = LoginManager()

# Callback route to reload user from userID in session
@login_manager.user_loader
def load_user(id):
    return UserLogin.get(id)


# Logic to login user with query to database
def session_login(token):
    user_info = token["userinfo"]

    user = db.session.scalars(
        db.select(User).filter_by(email=user_info["email"])
    ).one_or_none()

    if not user:
        user_nickname = (
            user_info["given_name"]
            if "given_name" in user_info
            else user_info["nickname"]
        )
        user = User(
            id=str(uuid4()),
            email=user_info["email"],
            name=user_info["name"],
            nickname=user_nickname,
        )
        db.session.add(user)
    db.session.commit()

    session["is_authenticated"] = True
    return login_user(UserLogin(user))


class UserLogin(UserMixin):
    def __init__(self, user):
        self.id = user.id
        self.name = user.name
        self.nickname = user.nickname
        self.email = user.email

    def __repr__(self):
        return "%s %s %s" % (self.id, self.name, self.email)

    def get(id):
        return UserLogin(User.find_item(id))
