from typing import Sequence

from sqlalchemy import select
from sqlalchemy.inspection import inspect

from movie_web.db_models import Movie, User, db

REQUIRED_MOVIE_KEYS = [column.key for column in inspect(Movie).attrs][3:]  # type: ignore


def get_user_by_name(name) -> User | None:
    stmt = select(User).where(User.user_name == name)
    user = db.session.scalar(stmt)
    print(user)
    if user:
        print(user.movies)
    return user


def get_all_movies() -> Sequence[Movie]:
    stmt = select(Movie).order_by(Movie.id)
    return db.session.execute(stmt).scalars().all()


def add_movie(movie):
    db.session.add(movie)
    db.session.commit()


def add_movie_to_user(user, movie):
    user.movies.append(movie)
    db.session.commit()


def get_movie_by_id(movie_id):
    return db.session.get(Movie, movie_id)


def get_movie_by_imdb_id(imdb_id) -> Movie | None:
    stmt = select(Movie).where(Movie.imdb_id == imdb_id)
    return db.session.scalar(stmt)


def update_movie(movie, form_data):
    data = form_data.to_dict()
    for key, value in data.items():
        setattr(movie, key, value)


def refresh_movie(movie, refreshed_movie):
    for key in REQUIRED_MOVIE_KEYS:
        value = getattr(refreshed_movie, key)
        setattr(movie, key, value)
    db.session.commit()


def check_for_errors(form_data) -> str | None:
    data = form_data.to_dict()
    print("DATA:", data)

    for key in REQUIRED_MOVIE_KEYS:
        if key not in data:
            return f"{key.capitalize()} is required!"

    for key in data:
        if not hasattr(Movie, key):
            return f"Movie has no attribute called --{key}--"

    return None


def serialize_omdb_movie(omdb_response: dict) -> Movie:
    if not omdb_response:
        raise ValueError("OMDB response is empty!")

    # Extract and transform data
    poster = omdb_response.get("Poster")
    if poster:
        # get bigger poster image
        poster = poster.replace("SX300", "SX500")

    imdb_rating = omdb_response.get("imdbRating", 0)
    if imdb_rating == "N/A":
        imdb_rating = 0
    movie_data = {
        "title": omdb_response.get("Title"),
        "year": int(omdb_response.get("Year", 0)),  # Convert Year to integer
        "genre": omdb_response.get("Genre"),
        "imdb_id": omdb_response.get("imdbID"),
        "stars": omdb_response.get("Actors"),
        "director": omdb_response.get("Director"),
        "writer": omdb_response.get("Writer"),
        "plot": omdb_response.get("Plot"),
        "poster_link": poster,
        "imdb_rating": float(imdb_rating),  # Convert Rating to float
    }

    # Ensure required fields are present
    required_fields = {"title", "year", "imdb_id"}
    missing_fields = [
        field for field in required_fields if not movie_data.get(field)
    ]
    if missing_fields:
        raise ValueError(
            f"Missing required fields: {', '.join(missing_fields)}"
        )

    # Create a Movie object with the extracted data
    new_movie = Movie(**movie_data)
    return new_movie


def add_review(review):
    db.session.add(review)
    db.session.commit()
