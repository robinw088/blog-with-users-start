from flask import Flask, render_template, redirect, url_for, flash,abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm, RegisterForm, LogINForm,CommentForm
from flask_gravatar import Gravatar
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap(app)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)


gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

##CONFIGURE TABLES

class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    author_id=db.Column(db.Integer, db.ForeignKey('user.id'))
    author = relationship("User", back_populates="posts")
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    comments = relationship("Comment", back_populates="parent_post")

class Comment(db.Model):
    __tablename__="comment"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    comment_author=relationship("User", back_populates="comments")
    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comments")

    text = db.Column(db.Text, nullable=False)

class User(UserMixin,db.Model):
    __tablename__ ="user"
    id = db.Column(db.Integer, primary_key=True)
    email= db.Column(db.String(250), nullable=False)
    password= db.Column(db.String(250), nullable=False)
    name= db.Column(db.String(250), nullable=False)
    posts = relationship("BlogPost", back_populates="author")
    comments=relationship("Comment", back_populates="comment_author")
db.create_all()

def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            if current_user.id !=1:
                abort(403, description="The access to the requested resource is forbidden. The server understood the request, but will not fulfill it due to client-related issues.")
        else:
            abort(403, description="The access to the requested resource is forbidden. The server understood the request, but will not fulfill it due to client-related issues.")
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def get_all_posts():
    userid=0
    posts = BlogPost.query.all()

    if current_user.is_authenticated:
        userid=current_user.id
    return render_template("index.html", all_posts=posts, is_loggedin=current_user.is_authenticated, id=userid)



@app.route('/register', methods=['get','post'])
def register():
    form=RegisterForm()
    if form.validate_on_submit():
        data=User(email=form.email.data,
                  password=generate_password_hash(form.password.data,method='pbkdf2:sha256',salt_length=8),
                  name=form.name.data,

        )
        if User.query.filter_by(email=form.email.data).first():
            flash("Register Failed: This email address has already registed")
            return redirect(url_for('register'))
        else:
            db.session().add(data)
            db.session().commit()
            login_user(data)
            return redirect(url_for('get_all_posts'))
    return render_template("register.html", form=form, is_loggedin=current_user.is_authenticated)


@app.route('/login', methods=['get','post'])
def login():
    form=LogINForm()
    if form.validate_on_submit():
        user=User.query.filter_by(email=form.email.data).first()
        if user:
            if check_password_hash(user.password,form.password.data):
                login_user(user)
                return redirect(url_for('get_all_posts'))
            else:
                flash('Password does not match')
                redirect(url_for('login'))
        else:
            flash('Email does not exist in the database')
            redirect(url_for('login'))
    return render_template("login.html", form=form, is_loggedin=current_user.is_authenticated)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>", methods=['post','get'])
def show_post(post_id):
    userid=0
    requested_post = BlogPost.query.get(post_id)
    form = CommentForm()
    if form.validate_on_submit():
        if current_user.is_authenticated:
            userid = current_user.id
            data = Comment(text=form.comment.data,
                           comment_author=current_user,
                           parent_post=requested_post, )
            db.session.add(data)
            db.session.commit()
        else:
            flash("please login to comment the blog")
            return redirect(url_for('login'))

    return render_template("post.html", post=requested_post, is_loggedin=current_user.is_authenticated, id=userid,
                           form=form)


@app.route("/about")
def about():
    return render_template("about.html", is_loggedin=current_user.is_authenticated)


@app.route("/contact")
def contact():
    return render_template("contact.html", is_loggedin=current_user.is_authenticated)


@app.route("/new-post", methods=['post', 'get'])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form, is_loggedin=current_user.is_authenticated)


@app.route("/edit-post/<int:post_id>")
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = edit_form.author.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id, is_loggedin=current_user.is_authenticated))

    return render_template("make-post.html", form=edit_form, is_loggedin=current_user.is_authenticated)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'), is_loggedin=current_user.is_authenticated)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
