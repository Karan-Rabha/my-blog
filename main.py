from datetime import date
from flask import Flask,render_template,redirect, request,url_for, flash, abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from functools import wraps
from forms import CreatePostForm, RegistrationForm, LoginForm, ContactForm
import os


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
ckeditor = CKEditor(app)
Bootstrap(app)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL",  "sqlite:///blog.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1000))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    posts = relationship('BlogPost', back_populates='posted_by')


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    posted_by = relationship('User', back_populates="posts")

# db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def admin_only(func):
    @wraps(func)
    def warper(*args, **kwargs):
        user = current_user.get_id()
        if user:
            if int(user) == 1 or int(user) == 2:
                return func(*args, **kwargs)
        return abort(403)
    return warper


@app.route("/")
def home():
    posts = BlogPost.query.all()[::-1]
    return render_template("index.html", all_posts=posts, logged_in=current_user)


@app.route("/create-blog",methods=['GET','POST'])
def create_post():
    if current_user.is_authenticated:
        form = CreatePostForm()
        if request.method == "POST" and form.validate_on_submit():
            new_post = BlogPost(
                title = form.title.data,
                subtitle = form.subtitle.data,
                body = form.body.data,
                date=date.today().strftime("%B %d, %Y"),
                posted_by = current_user,
            )
            db.session.add(new_post)
            db.session.commit()
            return redirect(url_for('home'))
        return render_template("post.html", form=form, logged_in=current_user, edit_post=False)
    else:
        flash("You need to be signed in to make a post")
        return redirect(url_for('home'))


@app.route("/post/<int:post_id>")
def post(post_id):
    selected_post = BlogPost.query.get(post_id)
    return render_template("showpost.html",post=selected_post,logged_in=current_user)


@app.route("/edit-post/<int:post_id>", methods=['GET', 'POST'])
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        body=post.body
    )
    if request.method == "POST" and edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for('post', post_id=post.id))
    return render_template("post.html",form=edit_form, edit_post=True, logged_in=current_user)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('home'))

@app.route("/contact", methods=['GET', 'POST'])
def contact():
    contact_form = ContactForm()
    if request.method == 'POST' and contact_form.validate_on_submit():
        flash(f"Hello {contact_form.name.data} its nice to hear from you i will contact you soon!!")
        return redirect(url_for("contact"))
    return render_template("contact.html", form=contact_form, logged_in=current_user)


@app.route("/about")
def about():
    return render_template("about.html", logged_in=current_user)


@app.route("/login", methods=['GET', 'POST'])
def signin():
    loginform = LoginForm()
    if request.method == 'POST' and loginform.validate_on_submit():
        form_email = loginform.data.get('email')
        user = User.query.filter_by(email=form_email).first()
        if user:
            if check_password_hash(pwhash=user.password, password=loginform.data.get('password')):
                login_user(user)
                return redirect(url_for("home"))
            else:
                flash('Password incorrect,please try again.')
        else:
            flash('That Email does not exist,please try again.')
            return redirect(url_for("signin"))
    return render_template("login.html", form=loginform ,logged_in=current_user)


@app.route("/signup", methods=['GET', 'POST'])
def register():
    registrationform = RegistrationForm()
    if request.method == 'POST' and registrationform.validate_on_submit():
        form_email = registrationform.data['email']
        user = User.query.filter_by(email=form_email).first()
        if user:
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for("signin"))
        else:
            new_user = User(
                email=registrationform.data['email'],
                password=generate_password_hash(
                    password=registrationform.data['password'], method="pbkdf2:sha256", salt_length=8),
                name=registrationform.data['name'],
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for("home"))
    return render_template("register.html",form=registrationform ,logged_in=current_user)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))




if __name__ == "__main__":
    app.run(debug=True)