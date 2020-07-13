"""Example flask app that stores passwords hashed with Bcrypt. Yay!"""

from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User,Feedback
from forms import RegisterForm, LoginForm, FeedbackForm, DeleteForm
from werkzeug.exceptions import Unauthorized

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "postgres:///feedback"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "QWS456"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

connect_db(app)
db.create_all()

toolbar = DebugToolbarExtension(app)


@app.route("/")
def homepage():
    """Show homepage with links to site areas."""

    return redirect("/register")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user: produce form & handle form submission."""

    form = RegisterForm()

    if form.validate_on_submit():
        username = form.username.data
        pwd = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data

        user = User.register(username, pwd, email, first_name, last_name)
        db.session.add(user)
        db.session.commit()

        session["username"] = user.username

        # on successful login, redirect to secret page
        return redirect(f"/users/{user.username}")

    else:
        return render_template("users/register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    """show login form or handle login."""
    if "username" in session:
        return redirect(f"/users/{session['username']}")

    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        pwd = form.password.data

        # authenticate will return a user or False
        user = User.authenticate(username, pwd)

        if user:
            flash(f" Welcome Back, {user.username}")
            session["username"] = user.username 
            return redirect(f"/users/{user.username}")

        else:
            form.username.errors = ["Wrong username/password"]
            return render_template("users/login.html", form=form)

    return render_template("users/login.html", form=form)


@app.route("/users/<username>")
def show_user_details(username):
    """Show details for logged-in users only."""

    if "username" not in session or username != session['username']:
        flash("You must be logged in to view!")
        raise Unauthorized()

    else:
        user = User.query.get_or_404(username)
        form = DeleteForm()
    
        return render_template("/users/show_user.html", user = user, form = form)


@app.route("/logout")
def logout():
    """Logs user out and redirects to login page."""

    session.pop("username")

    return redirect("/login")


@app.route("/users/<username>/delete", methods=["POST"])
def delete_user(username):
    """ Delete user and redirect to login """

    if username != session['username'] or "username" not in session:
        raise Unauthorized()

    user = User.query.get_or_404(username)
    db.session.delete(user)
    db.session.commit()
    session.pop("username")

    return redirect("/login")


@app.route("/users/<username>/feedback/new", methods=["GET","POST"])
def new_feedback(username):
    """ Add data to table from feedback form """

    if username!= session['username'] or "username" not in session:
        raise Unauthorized()

    form = FeedbackForm()

    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data

        feedback = Feedback(title = title, content=content, username = username)

        db.session.add(feedback)
        db.session.commit()
        return redirect(f"/users/{feedback.username}")

    else:
        return render_template("/feedback/new.html", form = form)

    
@app.route("/feedback/<int:feedback_id>/update", methods=["GET","POST"])
def update_feedback(feedback_id):
    """ Update the feedback from form """
    feedback = Feedback.query.get(feedback_id)

    if feedback.username != session['username'] or "username" not in session:
        raise Unauthorized()
    
    form = FeedbackForm(obj=feedback)

    if form.validate_on_submit():
        feedback.title = form.title.data
        feedback.content = form.content.data
        db.session.commit()

        return redirect(f"/users/{feedback.username}")

    return render_template("/feedback/edit.html", form=form, feedback=feedback)


@app.route("/feedback/<int:feedback_id>/delete", methods=["POST"])
def delete_feedback(feedback_id):
    """ Delete feedback if username is in session """
    feedback = Feedback.query.get(feedback_id)

    if feedback.username != session['username'] or "username" not in session:
        raise Unauthorized()
    
    form = DeleteForm()

    if form.validate_on_submit():
        db.session.delete(feedback) 
        db.session.commit()

    return redirect(f"/users/{feedback.username}")

@app.errorhandler(404)
def page_not_found(error):
    """Show 404 ERROR page if page NOT FOUND"""

    return render_template("error.html"), 404

@app.errorhandler(401)
def page_not_logged(error):
    """ Show 401 Error page if not logged in """
    flash("Please login here")
    return redirect("/login")