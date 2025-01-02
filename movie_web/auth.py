import functools

from flask import (
    Blueprint,
    Response,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash
from werkzeug.wrappers.response import Response  # noqa: F811

from movie_web import db_manager
from movie_web.db_models import User, db

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/register", methods=("GET", "POST"))
def register() -> Response | str:
    """
    Handle user registration.

    :return: A Flask response or rendered registration template.
    :rtype: flask.Response
    """
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        error = None

        if not username:
            error = "Username is required."
        elif not password:
            error = "Password is required."

        if error is None:
            try:
                db_manager.create_user(username, password)
            except IntegrityError:
                error = f"User {username} is already registered."
                db.session.rollback()
            else:
                message = f"User {username} successfully created!"
                flash(message=message, category="info")
                return redirect(url_for("auth.login"))

        flash(message=error, category="error")

    return render_template("auth/register.html")


@bp.route("/login", methods=("GET", "POST"))
def login() -> Response | str:
    """
    Handle user login.

    :return: A Flask response or rendered login template.
    :rtype: flask.Response
    """
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        error = None

        user = db_manager.get_user_by_name(username)

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


@bp.before_app_request
def load_logged_in_user() -> None:
    """
    Load the logged-in user into the global object.

    :return: None
    """
    user_id = session.get("user_id")

    if user_id is None:
        g.user = None
    else:
        g.user = db.session.get(User, user_id)


@bp.route("/logout")
def logout() -> Response:
    """
    Log out the current user.

    :return: A redirect to the index page.
    :rtype: flask.Response
    """
    session.clear()
    return redirect(url_for("index"))


def login_required(view):
    """
    Decorator to enforce login requirement for a view.

    :param view: The view function to wrap.
    :type view: callable
    :return: Wrapped view function.
    :rtype: callable
    """

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            abort(401)
            return redirect(url_for("auth.login"))

        return view(**kwargs)

    return wrapped_view
