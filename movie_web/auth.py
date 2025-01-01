import functools

from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from movie_web.db_manager import get_user_by_name
from movie_web.db_models import User, db

bp = Blueprint("auth", __name__, url_prefix="/auth")


# @bp.route associates the URL /register with the register view function. When Flask receives a request to /auth/register, it will call the register view and use the return value as the response.

# If the user submitted the form, request.method will be 'POST'. In this case, start validating the input.

# request.form is a special type of dict mapping submitted form keys and values. The user will input their username and password.

# Validate that username and password are not empty.

# If validation succeeds, insert the new user data into the database.

# db.execute takes a SQL query with ? placeholders for any user input, and a tuple of values to replace the placeholders with. The database library will take care of escaping the values so you are not vulnerable to a SQL injection attack.

# For security, passwords should never be stored in the database directly. Instead, generate_password_hash() is used to securely hash the password, and that hash is stored. Since this query modifies data, db.commit() needs to be called afterwards to save the changes.

# An sqlite3.IntegrityError will occur if the username already exists, which should be shown to the user as another validation error.

# After storing the user, they are redirected to the login page. url_for() generates the URL for the login view based on its name. This is preferable to writing the URL directly as it allows you to change the URL later without changing all code that links to it. redirect() generates a redirect response to the generated URL.

# If validation fails, the error is shown to the user. flash() stores messages that can be retrieved when rendering the template.


# When the user initially navigates to auth/register, or there was a validation error, an HTML page with the registration form should be shown. render_template() will render a template containing the HTML, which you’ll write in the next step of the tutorial.
@bp.route("/register", methods=("GET", "POST"))
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        # db = get_db()
        error = None

        if not username:
            error = "Username is required."
        elif not password:
            error = "Password is required."

        if error is None:
            try:
                hashed_pw = generate_password_hash(password)
                new_user = User(user_name=username, password=hashed_pw)  # type: ignore
                db.session.add(new_user)
                db.session.commit()
            except IntegrityError:
                error = f"User {username} is already registered."
                db.session.rollback()
            else:
                return redirect(url_for("auth.login"))

        flash(message=error, category="error")

    return render_template("auth/register.html")


# There are a few differences from the register view:

# The user is queried first and stored in a variable for later use.

# fetchone() returns one row from the query. If the query returned no results, it returns None. Later, fetchall() will be used, which returns a list of all results.

# check_password_hash() hashes the submitted password in the same way as the stored hash and securely compares them. If they match, the password is valid.

# session is a dict that stores data across requests. When validation succeeds, the user’s id is stored in a new session. The data is stored in a cookie that is sent to the browser, and the browser then sends it back with subsequent requests. Flask securely signs the data so that it can’t be tampered with.


# Now that the user’s id is stored in the session, it will be available on subsequent requests. At the beginning of each request, if a user is logged in their information should be loaded and made available to other views.
@bp.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        # db = get_db()
        error = None
        user = get_user_by_name(username)

        if user is None:
            error = "Incorrect username."
        elif not check_password_hash(user.password, password):
            error = "Incorrect password."

        if error is None:
            session.clear()
            session["user_id"] = user.id  # type: ignore
            return redirect(url_for("index"))

        flash(message=error, category="error")

    return render_template("auth/login.html")


# bp.before_app_request() registers a function that runs before the view function, no matter what URL is requested. load_logged_in_user checks if a user id is stored in the session and gets that user’s data from the database, storing it on g.user, which lasts for the length of the request. If there is no user id, or if the id doesn’t exist, g.user will be None.
@bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")

    if user_id is None:
        g.user = None
    else:
        g.user = db.session.get(User, user_id)


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))

        return view(**kwargs)

    return wrapped_view
