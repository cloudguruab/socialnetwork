from flask_wtf import FlaskForm
from models import User
from wtforms import StringField, PasswordField, TextAreaField
from wtforms.validators import (DataRequired, Regexp, ValidationError, Email,
EqualTo, Length)


def name_exists(form, field): # NOTE validator makes sure our data matches a certain pattern. 
    """writing our own validator."""
    if User.select().where(User.username == field.data).exists():
        raise ValidationError("User with that name already exist.")


def email_exists(form, field):
    if User.select().where(User.email == field.data).exists():
        raise ValidationError("That email already exist")


class RegisterForm(FlaskForm):
    username = StringField(
        'Username', 
        validators=[
            DataRequired(), 
            Regexp(r'^[a-zA-Z0-9_]+$', 
            message=("Username shourld be one word, letters, numbers, and underscores only.")),
            name_exists
        ]
    )
    email = StringField(
        'Email', 
        validators=[
            DataRequired(), 
            Email(), 
            email_exists
        ]
    )
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(),
            Length(min=5),
            EqualTo('password2', message='Passwords must match')
        ]
    )
    password2 = PasswordField(
        'Confirm Password',
        validators=[DataRequired()]
    )


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])


class PostForm(FlaskForm): # NOTE issue with displaying text content. 
    content = TextAreaField('value')