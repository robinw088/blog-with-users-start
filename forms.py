from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL,length
from flask_ckeditor import CKEditorField

##WTForm
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")

class RegisterForm(FlaskForm):
    email=StringField("Email", validators=[DataRequired()])
    password=PasswordField("Password", validators=[DataRequired(),length(min=4)])
    name=StringField("Name", validators=[DataRequired()])
    register = SubmitField("Register")

class LogINForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired(), length(min=4)])
    login = SubmitField("Log in")

class CommentForm(FlaskForm):
    comment=CKEditorField("Comment",validators=[DataRequired()])
    submit = SubmitField("Submit Comment")
