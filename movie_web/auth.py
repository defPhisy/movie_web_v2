import functools

from flask import (
    Blueprint,
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
from werkzeug.security import check_password_hash, generate_password_hash

from movie_web.db_manager import get_user_by_name
from movie_web.db_models import User, db

bp = Blueprint("auth", __name__, url_prefix="/auth")


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
            abort(401)
            # return redirect(url_for("auth.login"))

        return view(**kwargs)

    return wrapped_view
