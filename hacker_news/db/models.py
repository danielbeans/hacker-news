from . import db
from flask_login import UserMixin


class SearchMixin:
    @classmethod
    def find_item(cls, id):
        item = db.session.scalars(db.select(cls).filter_by(id=id)).one_or_none()
        return item

    @classmethod
    def get_all(cls):
        items = db.session.scalars(db.select(cls)).all()
        return items


class WebsiteSetting(SearchMixin, db.Model):
    __tablename__ = "website_settings"

    id = db.Column(db.String, primary_key=True)
    status = db.Column(db.String, default="")


class User(UserMixin, SearchMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String, unique=True)
    name = db.Column(db.String)
    nickname = db.Column(db.String)
    liked_top_stories = db.relationship("TopStoryAssociation", backref="user")
    liked_new_stories = db.relationship("NewStoryAssociation", backref="user")

    def __repr__(self):
        return f"<User {self.id} {self.name} {self.email}>"

    def like_story(self, story_id, story_type, action, type):
        user = User.find_item(self.id)
        if story_type == "top_story":
            with db.session.no_autoflush:
                if found_story_association := self.has_liked_story(story_id):
                    db.session.delete(found_story_association)
                    db.session.commit()
                if action == "add":
                    liked = TopStoryAssociation(type=type)
                    liked.story = TopStory.find_item(story_id)
                    user.liked_top_stories.append(liked)
        elif story_type == "new_story":
            with db.session.no_autoflush:
                if found_story_association := self.has_liked_story(story_id):
                    db.session.delete(found_story_association)
                    db.session.commit()
                if action == "add":
                    liked = NewStoryAssociation(type=type)
                    liked.story = NewStory.find_item(story_id)
                    user.liked_new_stories.append(liked)
                db.session.commit()
        db.session.commit()

    def has_liked_story(self, story_id):
        top_story = db.session.scalars(
            db.select(TopStoryAssociation).filter(
                TopStoryAssociation.user_id.like(self.id),
                TopStoryAssociation.story_id.like(story_id),
            )
        ).one_or_none()
        new_story = db.session.scalars(
            db.select(NewStoryAssociation).filter(
                NewStoryAssociation.user_id.like(self.id),
                NewStoryAssociation.story_id.like(story_id),
            )
        ).one_or_none()
        return top_story or new_story


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


# For like/dislike functionality
class TopStoryAssociation(SearchMixin, db.Model):
    __tablename__ = "top_story_association_table"

    user_id = db.Column(db.ForeignKey("user.id"), primary_key=True)
    story_id = db.Column(db.ForeignKey("top_stories.id"), primary_key=True)
    story = db.relationship("TopStory", backref="story")
    type = db.Column(db.String)

    def __repr__(self):
        return f"<TopStoryID: {self.user_id}> {self.story_id}"


# For like/dislike functionality
class NewStoryAssociation(SearchMixin, db.Model):
    __tablename__ = "new_story_association_table"

    user_id = db.Column(db.ForeignKey("user.id"), primary_key=True)
    story_id = db.Column(db.ForeignKey("new_stories.id"), primary_key=True)
    story = db.relationship("NewStory", backref="story")
    type = db.Column(db.String)

    def __repr__(self):
        return f"<NewStoryID: {self.user_id}> {self.story_id}"


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
