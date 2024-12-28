from datetime import datetime, timezone

from flask import (
    Blueprint,
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
from movie_web.db_models import Review, db

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
            flash(error)
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

            return redirect(url_for("blog.index"))

    return render_template("blog/create.html")


@bp.route("/movie/<int:movie_id>")
def movie_details(movie_id):
    movie = db_manager.get_movie_by_id(movie_id)
    user_review = next(
        (review for review in g.user.reviews if review.movie_id == movie_id),
        None,
    )
    stars = utils.calculate_imdb_stars(movie.imdb_rating)  # type: ignore

    return render_template(
        "blog/movie.html", movie=movie, user_review=user_review, stars=stars
    )


@bp.route("/movie/<int:movie_id>/update", methods=("GET", "POST"))
@login_required
def update_movie(movie_id):
    movie = db_manager.get_movie_by_id(movie_id)
    g.now = datetime.now()

    if request.method == "POST":
        error = db_manager.check_for_errors(request.form)

        if error is not None:
            flash(error)
        else:
            db_manager.update_movie(movie, request.form)
            db.session.commit()
            return redirect(url_for("blog.index"))

    return render_template(
        "blog/update.html",
        movie=movie,
        movie_keys=db_manager.REQUIRED_MOVIE_KEYS,
    )


@bp.route("/movie/<int:movie_id>/delete", methods=("POST",))
@login_required
def delete_movie(movie_id):
    movie = db_manager.get_movie_by_id(movie_id)

    g.user.movies.remove(movie)
    db.session.commit()

    return redirect(url_for("blog.index"))


@bp.route("/movie/<int:movie_id>/refresh", methods=("POST",))
def refresh_movie(movie_id):
    movie = db_manager.get_movie_by_id(movie_id)
    imdb_id = movie.imdb_id  # type: ignore

    requested_movie = omdb_api.get_movie(imdb_id=imdb_id)
    refreshed_movie = db_manager.serialize_omdb_movie(requested_movie)

    db_manager.refresh_movie(movie, refreshed_movie)

    return redirect(url_for("blog.index"))


@bp.route("/movie/<int:movie_id>/review", methods=("POST",))
def add_review(movie_id):
    new_review = Review(
        user_id=g.user.id,  # type: ignore
        movie_id=movie_id,  # type: ignore
        text="test",  # type: ignore
        rating=4,  # type: ignore
        created=datetime.now(timezone.utc),  # type: ignore
    )

    db_manager.add_review(new_review)
    db.session.commit()

    return redirect(url_for("blog.index"))
