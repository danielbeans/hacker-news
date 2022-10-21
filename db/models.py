from . import db


class SearchMixin:
    @classmethod
    def find_item(cls, id):
        item = db.session.scalars(db.select(cls).filter_by(id=id)).one_or_none()
        return item


class User(SearchMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String, unique=True)
    name = db.Column(db.String)
    nickname = db.Column(db.String)

    def __init__(self, id, email, name, nickname):
        self.id = id
        self.email = email
        self.name = name
        self.nickname = nickname

    def __repr__(self):
        return f"<User {self.email}>"


class StoryModel(SearchMixin, db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    score = db.Column(db.Integer)
    time = db.Column(db.Integer)
    author = db.Column(db.String)
    url = db.Column(db.String)

    def __repr__(self):
        return f"<ID {self.id}> {self.title}"


class NewStory(StoryModel):
    __tablename__ = "new_stories"

    def __init__(self, id, title, score, time, author, url):
        self.id = id
        self.title = title
        self.score = score
        self.time = time
        self.author = author
        self.url = url


class TopStory(StoryModel):
    __tablename__ = "top_stories"

    order_num = db.Column(db.Integer)

    def __init__(self, id, title, score, time, author, url, order_num):
        self.id = id
        self.title = title
        self.score = score
        self.time = time
        self.author = author
        self.url = url
        self.order_num = order_num
