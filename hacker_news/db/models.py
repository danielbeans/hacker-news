"""
Defines all models for SQLAlchemy and the database
"""

from flask_login import UserMixin
from . import db


class SearchMixin:
    """
    A mixin class that implements searching for itself in the database

    Methods:
        find_item(cls, id): Find item in database and return it
        get_all(cls): Get all of item from database and return them
    """

    @classmethod
    def find_item(cls, id):
        item = db.session.scalars(db.select(cls).filter_by(id=id)).one_or_none()
        return item

    @classmethod
    def get_all(cls):
        items = db.session.scalars(db.select(cls)).all()
        return items


class WebsiteSetting(SearchMixin, db.Model):
    """
    A class that models the website_setting table

    Attributes:
        id: Key of setting
        status: Value of setting
    """

    __tablename__ = "website_settings"

    id = db.Column(db.String, primary_key=True)
    status = db.Column(db.String, default="")


class User(UserMixin, SearchMixin, db.Model):
    """
    The User class that implements both an SQLAlchemy base and Flask_login base

    Attributes:
        id: User ID
        email: User email
        name: User name
        nickname: User name or email
        role: Member or Admin
        liked_stories: Stories the User has liked

    Methods:
        like_story(self, story_id, action, type): Make a User like/dislike a story
        has_liked_story(self, story_id): Finds if the User has liked a story
    """

    __tablename__ = "user"

    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String, unique=True)
    name = db.Column(db.String)
    nickname = db.Column(db.String)
    role = db.Column(db.String)
    liked_stories = db.relationship("StoryAssociation", backref="user")

    def __repr__(self):
        return f"<User {self.id} {self.name} {self.email}>"

    def like_story(self, story_id, action, type):
        user = User.find_item(self.id)
        with db.session.no_autoflush:
            if found_story_association := self.has_liked_story(story_id):
                db.session.delete(found_story_association)
                db.session.commit()
            if action == "add":
                liked = StoryAssociation(type=type)
                liked.story = Story.find_item(story_id)
                user.liked_stories.append(liked)
        db.session.commit()

    def has_liked_story(self, story_id):
        story = db.session.scalars(
            db.select(StoryAssociation).filter(
                StoryAssociation.user_id.like(self.id),
                StoryAssociation.story_id.like(story_id),
            )
        ).one_or_none()
        return story


class Story(SearchMixin, db.Model):
    """
    The Story class that models for the stories table

    Attributes:
        id: Story ID
        title: Story title
        score: Story score
        time: Time story was published in Unix time
        author: Story author
        url: Story url
        num_comments: Number of comments a Story has
        order_num: The order of the story when fetched
        keywords: Story keywords
        comments: Story comments
    """

    __tablename__ = "stories"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    score = db.Column(db.Integer)
    time = db.Column(db.Integer)
    author = db.Column(db.String)
    url = db.Column(db.String)
    num_comments = db.Column(db.Integer)
    order_num = db.Column(db.Integer)
    keywords = db.Column(db.String)
    comments = db.relationship(
        "Comment", cascade="all, delete, delete-orphan", backref="story"
    )

    def __repr__(self):
        return f"<ID {self.id}> {self.title}"


# For like/dislike functionality
class StoryAssociation(db.Model):
    """
    The class that defines the many to many relationship between a User and story

    Attributes:
        user_id: User ID
        story_id: Story ID
        story: Story object
        type: If the User has liked or disliked the Story

    Methods:
        find_item_story_id(cls, id): Find StoryAssociation by story ID
        find_item_user_id(cls, id): Find StoryAssociation by user ID
    """

    __tablename__ = "story_association_table"

    user_id = db.Column(db.ForeignKey("user.id"), primary_key=True)
    story_id = db.Column(db.ForeignKey("stories.id"), primary_key=True)
    story = db.relationship("Story", backref="story")
    type = db.Column(db.String)

    def __repr__(self):
        return f"<StoryID: {self.user_id}> {self.story_id}"

    @classmethod
    def find_item_story_id(cls, id):
        item = db.session.scalars(db.select(cls).filter_by(story_id=id)).one_or_none()
        return item

    @classmethod
    def find_item_user_id(cls, id):
        item = db.session.scalars(db.select(cls).filter_by(user_id=id)).one_or_none()
        return item


class Comment(SearchMixin, db.Model):
    """
    The Comment class that models for the comments table

    Attributes:
        id: Comment ID
        time: Time comment was published in Unix time
        author: Comment author
        text: Comment text
        type: A root or child comment
        story_id: Story comment belongs to if root
        parent_comment_id: Comment the comment belongs to if child
        comments: Comment comments
    """

    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.Integer)
    author = db.Column(db.String)
    text = db.Column(db.String)
    type = db.Column(db.String)
    story_id = db.Column(db.Integer, db.ForeignKey("stories.id"))
    parent_comment_id = db.Column(db.Integer, db.ForeignKey("comments.id"))
    comments = db.relationship(
        "Comment", backref=db.backref("parent_comment", remote_side="Comment.id")
    )

    def __repr__(self):
        return f"<ID {self.id}> {self.text}"
