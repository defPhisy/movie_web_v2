from datetime import datetime

from flask import (
    Blueprint,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)

import movie_web.db_manager as db_manager
import movie_web.omdb_api as omdb_api
import movie_web.utils as utils
from movie_web.auth import login_required
from movie_web.db_models import User, db

bp = Blueprint("blog", __name__)


@bp.route("/")
def index():
    user = g.user
    db_manager.get_all_movies()
    return render_template("blog/index.html", user=user)


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    if request.method == "POST":
        title = request.form.get("title", None)
        imdb_id = request.form.get("imdb_id", None)
        year = request.form.get("year", None)

        error = None

        if not (title or imdb_id):
            error = "You have to enter at least one field. Title or IMDB-ID"

        if (
            title
            and title.lower()
            in map(lambda movie: movie.title.lower(), g.user.movies)
            and year in map(lambda movie: movie.year, g.user.movies)
        ):
            error = "Title already in your library"

        elif imdb_id and imdb_id in map(
            lambda movie: movie.imdb_id, g.user.movies
        ):
            error = "Title already in your library"

        if error is not None:
            flash(message=error, category="error")
        else:
            requested_movie = omdb_api.get_movie(
                title=title, year=year, imdb_id=imdb_id
            )

            new_movie = db_manager.serialize_omdb_movie(requested_movie)
            existing_movie = db_manager.get_movie_by_imdb_id(new_movie.imdb_id)

            if not existing_movie:
                db_manager.add_movie(new_movie)
                db_manager.add_movie_to_user(g.user, new_movie)
            else:
                db_manager.add_movie_to_user(g.user, existing_movie)
            message = f"Movie {new_movie.title} added!"
            flash(message=message, category="info")

            return redirect(url_for("blog.index"))

    return render_template("blog/create.html")


@bp.route("/movie/<int:movie_id>")
@login_required
def movie_details(movie_id):
    movie = db_manager.get_movie_by_id(movie_id)
    if movie is None:
        abort(404)

    user_review = next(
        (review for review in g.user.reviews if review.movie_id == movie_id),
        None,
    )
    imdb_stars = utils.calculate_imdb_stars(movie.imdb_rating)  # type: ignore
    genres = movie.genre.split(",")  # type: ignore

    return render_template(
        "blog/movie.html",
        movie=movie,
        user_review=user_review,
        stars=imdb_stars,
        genres=genres,
    )


@bp.route("/movie/<int:movie_id>/update", methods=("GET", "POST"))
@login_required
def update_movie(movie_id):
    movie = db_manager.get_movie_by_id(movie_id)
    if movie is None:
        abort(404)
    g.now = datetime.now()

    if request.method == "POST":
        error = db_manager.check_for_errors(request.form)

        if error is not None:
            flash(message=error, category="error")
        else:
            db_manager.update_movie(movie, request.form)
            db.session.commit()
            return redirect(url_for("blog.movie_details", movie_id=movie.id))  # type: ignore

    return render_template(
        "blog/update.html",
        movie=movie,
        movie_keys=db_manager.REQUIRED_MOVIE_KEYS,
    )


@bp.route("/movie/<int:movie_id>/delete", methods=("POST",))
@login_required
def delete_movie(movie_id):
    movie = db_manager.get_movie_by_id(movie_id)
    if movie is None:
        abort(404)

    g.user.movies.remove(movie)
    db.session.commit()

    message = f"{movie.title} deleted!"  # type: ignore
    flash(message=message, category="delete")

    return redirect(url_for("blog.index"))


@bp.route("/movie/<int:movie_id>/refresh", methods=("POST",))
@login_required
def refresh_movie(movie_id):
    movie = db_manager.get_movie_by_id(movie_id)
    if movie is None:
        abort(404)

    imdb_id = movie.imdb_id  # type: ignore

    requested_movie = omdb_api.get_movie(imdb_id=imdb_id)
    refreshed_movie = db_manager.serialize_omdb_movie(requested_movie)

    db_manager.refresh_movie(movie, refreshed_movie)

    return redirect(url_for("blog.movie_details", movie_id=movie.id))  # type: ignore


@bp.route("/movie/<int:movie_id>/review", methods=("GET", "POST"))
@login_required
def add_review(movie_id):
    movie = db_manager.get_movie_by_id(movie_id)
    if movie is None:
        abort(404)

    if request.method == "POST":
        new_review = db_manager.create_review(g.user, movie_id)

        db_manager.add_review(new_review)
        flash(f"New Review by {g.user.user_name} created!", category="info")

        return redirect(url_for("blog.movie_details", movie_id=movie_id))

    return render_template("blog/add_review.html", movie=movie)


@bp.route("/review/<int:review_id>/update", methods=("GET", "POST"))
@login_required
def update_review(review_id):
    review = db_manager.get_review_by_id(review_id)
    if review is None:
        abort(404)

    movie = db_manager.get_movie_by_id(review.movie_id)
    g.now = datetime.now()

    if request.method == "POST":
        db_manager.update_review(review)

        return redirect(
            url_for("blog.movie_details", movie_id=review.movie_id)  # type: ignore
        )

    return render_template(
        "blog/update_review.html", review=review, movie=movie
    )


@bp.route("/review/<int:review_id>/delete", methods=("POST",))
@login_required
def delete_review(review_id):
    review = db_manager.get_review_by_id(review_id)

    if review is None:
        abort(404)

    db_manager.delete_review(review)
    message = f"Deleted Review from {g.user.user_name}!"
    flash(message, category="delete")

    return redirect(url_for("blog.movie_details", movie_id=review.movie_id))  # type: ignore


@bp.route("/user/<int:user_id>/delete", methods=("POST",))
@login_required
def delete_user(user_id):
    print("HERE")
    user = db.session.get(User, user_id)

    user_name = user.user_name  # type: ignore
    if user.id != g.user.id:  # type: ignore
        abort(403)

    db_manager.delete_user(user)
    message = f"User {user_name} successfully deleted!"
    flash(message, category="delete")

    return redirect(url_for("blog.index"))
