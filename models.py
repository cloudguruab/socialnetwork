import datetime

from flask_bcrypt import generate_password_hash
from flask_login import UserMixin
from peewee import *

DATABASE = SqliteDatabase("social.db")

class User(UserMixin, Model): # usermixin is a mixin that tells if user 
    # is logged in or not and gets their id
    username = CharField(unique=True)
    email = CharField(unique=True)
    password = CharField(max_length=100)
    joined_at = DateTimeField(default=datetime.datetime.now)
    is_admin = BooleanField(default=False)

    class Meta:
        database = DATABASE
        order_by = ('-joined_at',) # minus sign lets it 
                                   # know to order in desc order. 


    def get_post(self):
        """lets us grab out post."""
        return Post.select().where(Post.user == self)

    
    def get_stream(self):
        """lets us select the post we want."""
        return Post.select().where((Post.user == self) | (Post.user << self.following()))


    def following(self):
        """Lets us grab the users we follow."""
        return (User.select().join(
            Relationship, on=Relationship.to_user).where(
                Relationship.from_user == self
            )
        )


    def followers(self):
        """gets users that follow self"""
        return (
            User.select().join(
                Relationship, on=Relationship.from_user).where(
                    Relationship.to_user == self
                )
            )
        
    
    @classmethod # allows us to create an instance of the class from inside of it
    def create_user(cls, username, email, password, admin=False):
        try:
            with DATABASE.transaction():
                cls.create(
                    username=username, 
                    email=email,
                    password=generate_password_hash(password),
                    is_admin=admin
                )
        except IntegrityError:
            raise ValueError("User already exist")


class Post(Model):
    timestamp = DateTimeField(default=datetime.datetime.now)
    user = ForeignKeyField(User, backref='posts')
    # rel_model points to what model we are referring to. 
    # related_name is what the related model would call the model. 
    # ForeignKeyField - A field that points to another database record.
    content = TextField()

    class Meta:
        database = DATABASE
        order_by = ('-timestamp',) # here and above meta we use a comma because orderby needs to be a tuple. 
        # they wont be changed so thats why. It can be a list if we wanted to but tuples are immutable. 


class Relationship(Model):
    from_user = ForeignKeyField(User, backref='relationships')
    to_user = ForeignKeyField(User, backref='related_to')

    class Meta:
        database = DATABASE
        indexes = ((('from_user', 'to_user'), True),)

def initialize():
    DATABASE.connect()
    DATABASE.create_tables([User, Post, Relationship], safe=True)
    DATABASE.close()