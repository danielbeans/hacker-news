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

    def __repr__(self):
        return f"<User {self.email}>"


class Story(SearchMixin, db.Model):
    __abstract__ = True  # Prevents table from being created

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    score = db.Column(db.Integer)
    time = db.Column(db.Integer)
    author = db.Column(db.String)
    url = db.Column(db.String)
    num_comments = db.Column(db.Integer)

    def __repr__(self):
        return f"<ID {self.id}> {self.title}"


class NewStory(Story):
    __tablename__ = "new_stories"

    comments = db.relationship(
        "NewComment", cascade="all, delete, delete-orphan", backref="story"
    )


class TopStory(Story):
    __tablename__ = "top_stories"

    order_num = db.Column(db.Integer)
    comments = db.relationship(
        "TopComment", cascade="all, delete, delete-orphan", backref="story"
    )


class Comment(SearchMixin, db.Model):
    __abstract__ = True  # Prevents table from being created

    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.Integer)
    author = db.Column(db.String)
    text = db.Column(db.String)
    type = db.Column(db.String)

    def __repr__(self):
        return f"<ID {self.id}> {self.text}"


class NewComment(Comment):
    __tablename__ = "new_comments"

    story_id = db.Column(db.Integer, db.ForeignKey("new_stories.id"))
    parent_comment_id = db.Column(db.Integer, db.ForeignKey("new_comments.id"))
    comments = db.relationship(
        "NewComment", backref=db.backref("parent_comment", remote_side="NewComment.id")
    )


class TopComment(Comment):
    __tablename__ = "top_comments"

    story_id = db.Column(db.Integer, db.ForeignKey("top_stories.id"))
    parent_comment_id = db.Column(db.Integer, db.ForeignKey("top_comments.id"))
    comments = db.relationship(
        "TopComment", backref=db.backref("parent_comment", remote_side="TopComment.id")
    )
