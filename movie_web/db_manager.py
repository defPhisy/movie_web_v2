from datetime import datetime, timezone
from typing import Sequence

from flask import request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.inspection import inspect
from werkzeug.security import generate_password_hash

from movie_web import dummy_data, omdb_api
from movie_web.db_models import Movie, Review, User, db

REQUIRED_MOVIE_KEYS = [column.key for column in inspect(Movie).attrs][3:]  # type: ignore


def get_user_by_name(name: str) -> User | None:
    """
    Retrieve a user by their username.

    :param name: The username of the user.
    :return: The user object if found, otherwise None.
    """
    stmt = select(User).where(User.user_name == name)
    user = db.session.scalar(stmt)
    return user


def get_all_movies() -> Sequence[Movie]:
    """
    Get all movies from the database, ordered by movie ID.

    :return: A sequence of Movie objects.
    """
    stmt = select(Movie).order_by(Movie.id)
    return db.session.execute(stmt).scalars().all()


def add_movie(movie: Movie) -> None:
    """
    Add a movie to the database.

    :param movie: The movie object to be added.
    """
    db.session.add(movie)
    db.session.commit()


def add_movie_to_user(user: User, movie: Movie) -> None:
    """
    Add a movie to a user's movie list.

    :param user: The user object to which the movie will be added.
    :param movie: The movie object to be added.
    """
    user.movies.append(movie)
    db.session.commit()


def get_movie_by_id(movie_id: int) -> Movie | None:
    """
    Get a movie by its ID.

    :param movie_id: The ID of the movie.
    :return: The movie object if found, otherwise None.
    """
    return db.session.get(Movie, movie_id)


def get_movie_by_imdb_id(imdb_id: int) -> Movie | None:
    """
    Get a movie by its IMDb ID.

    :param imdb_id: The IMDb ID of the movie.
    :return: The movie object if found, otherwise None.
    """
    stmt = select(Movie).where(Movie.imdb_id == imdb_id)
    return db.session.scalar(stmt)


def update_movie(movie: Movie, form_data) -> None:
    """
    Update the attributes of a movie with form data.

    :param movie: The movie object to update.
    :param form_data: The form data containing new values.
    """
    data = form_data.to_dict()
    for key, value in data.items():
        setattr(movie, key, value)


def refresh_movie(movie: Movie, refreshed_movie: Movie) -> None:
    """
    Refresh a movie's data with the latest information.

    :param movie: The movie object to update.
    :param refreshed_movie: The new movie data to apply.
    """
    for key in REQUIRED_MOVIE_KEYS:
        value = getattr(refreshed_movie, key)
        setattr(movie, key, value)
    db.session.commit()


def check_for_errors(form_data) -> str | None:
    """
    Check for missing required fields in the form data.

    :param form_data: The form data to validate.
    :return: An error message if any required field is missing, otherwise None.
    """
    data = form_data.to_dict()

    for key in REQUIRED_MOVIE_KEYS:
        if key not in data:
            return f"{key.capitalize()} is required!"

    for key in data:
        if not hasattr(Movie, key):
            return f"Movie has no attribute called --{key}--"

    return None


def serialize_omdb_movie(omdb_response: dict) -> Movie:
    """
    Serialize an OMDB API response into a Movie object.

    :param omdb_response: The OMDB API response as a dictionary.
    :return: A Movie object populated with the OMDB data.
    :raises ValueError: If required fields are missing in the response.
    """
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


def get_review_by_id(review_id: int) -> Review | None:
    """
    Retrieve a review by its ID.

    :param review_id: The ID of the review.
    :return: The review object if found, otherwise None.
    """
    return db.session.get(Review, review_id)


def create_review(user_id: int, movie_id: int) -> Review:
    """
    Create a new review for a movie by a user.

    :param user_id: The ID of the user creating the review.
    :param movie_id: The ID of the movie being reviewed.
    :return: A new Review object.
    """
    return Review(
        user_id=user_id,  # type: ignore
        movie_id=movie_id,  # type: ignore
        text=request.form["text"],  # type: ignore
        rating=request.form["rating"],  # type: ignore
        created=datetime.now(timezone.utc),  # type: ignore
    )


def add_review(review: Review) -> None:
    """
    Add a review to the database.

    :param review: The review object to be added.
    """
    db.session.add(review)
    db.session.commit()


def update_review(review: Review) -> None:
    """
    Update an existing review with new data.

    :param review: The review object to be updated.
    """
    data = request.form.to_dict()
    for key, value in data.items():
        setattr(review, key, value)
    db.session.commit()


def delete_review(review: Review) -> None:
    """
    Delete a review from the database.

    :param review: The review object to be deleted.
    """
    db.session.delete(review)
    db.session.commit()


def create_user(username: str, password: str) -> User:
    """
    Create a new user and store it in the database.

    :param username: The username for the new user.
    :param password: The password for the new user.
    :return: The created user object.
    """
    hashed_pw = generate_password_hash(password)
    new_user = User(user_name=username, password=hashed_pw)  # type: ignore
    db.session.add(new_user)
    db.session.commit()

    return new_user


def delete_user(user: User) -> None:
    """
    Delete a user from the database.

    :param user: The user object to be deleted.
    """
    db.session.delete(user)
    db.session.commit()


def populate_dummy_data() -> None:
    """
    Populate the database with dummy data, including movies, users, and reviews.
    """
    # Populate movies
    for imdb_id in dummy_data.imdb_ids:
        omdb_response = omdb_api.get_movie(imdb_id=imdb_id)
        movie = serialize_omdb_movie(omdb_response)
        try:
            add_movie(movie)
        except IntegrityError:
            db.session.rollback()
            print(f"Movie with IMDb ID {imdb_id} already exists. Skipping...")

    # Populate users and assign movies
    for user_data in dummy_data.users:
        if get_user_by_name(user_data["user_name"]):
            continue
        user = create_user(user_data["user_name"], user_data["password"])

        for imdb_id in dummy_data.imdb_ids:
            movie = get_movie_by_imdb_id(imdb_id)  # type: ignore
            add_movie_to_user(user, movie)  # type: ignore

    # Populate reviews
    for user_reviews in dummy_data.reviews:
        for review_data in user_reviews:
            # Check for existing review
            if get_review_by_user_and_movie(
                review_data["user_id"], review_data["movie_id"]
            ):
                print(
                    f"Review by user {review_data['user_id']} for movie {review_data['movie_id']} already exists. Skipping..."
                )
                continue

            review = Review(
                user_id=review_data["user_id"],  # type: ignore
                movie_id=review_data["movie_id"],  # type: ignore # type: ignore
                text=review_data["text"],  # type: ignore # type: ignore
                rating=review_data["rating"],  # type: ignore
                created=review_data["created"],  # type: ignore
                updated=review_data["updated"],  # type: ignore
            )

            try:
                add_review(review)
            except IntegrityError:
                db.session.rollback()
                print(
                    f"Error adding review for movie {review_data['movie_id']} by user {review_data['user_id']}. Skipping..."
                )


def get_review_by_user_and_movie(user_id, movie_id):
    return (
        db.session.query(Review)
        .filter_by(user_id=user_id, movie_id=movie_id)
        .first()
    )
