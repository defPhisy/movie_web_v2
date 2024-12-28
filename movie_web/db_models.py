from datetime import datetime, timezone
from typing import List, Optional

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base, disable_autonaming=True)


class User(db.Model):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_name: Mapped[str] = mapped_column(String(30), unique=True)
    password: Mapped[str] = mapped_column(nullable=False)

    # Relationships
    movies: Mapped[List["Movie"]] = relationship(
        "Movie", secondary="user_movie", back_populates="users"
    )
    reviews: Mapped[List["Review"]] = relationship(
        "Review", back_populates="user", cascade="all, delete-orphan"
    )


class Movie(db.Model):
    __tablename__ = "movie"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(nullable=False)
    year: Mapped[int]
    genre: Mapped[str]
    imdb_id: Mapped[str] = mapped_column(unique=True)
    stars: Mapped[str]
    director: Mapped[str]
    writer: Mapped[str]
    plot: Mapped[str]
    poster_link: Mapped[str]
    imdb_rating: Mapped[float]

    # Relationships
    users: Mapped[List["User"]] = relationship(
        "User", secondary="user_movie", back_populates="movies"
    )
    reviews: Mapped[List["Review"]] = relationship(
        "Review", back_populates="movie", cascade="all, delete-orphan"
    )


class Review(db.Model):
    __tablename__ = "review"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    movie_id: Mapped[int] = mapped_column(ForeignKey("movie.id"))
    text: Mapped[Optional[str]]
    rating: Mapped[int] = mapped_column(
        CheckConstraint("rating >= 1 AND rating <= 10")
    )
    created: Mapped[datetime] = mapped_column(
        default=datetime.now(timezone.utc)
    )
    updated: Mapped[Optional[datetime]]

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="reviews")
    movie: Mapped["Movie"] = relationship("Movie", back_populates="reviews")

    def __repr__(self) -> str:
        return f"Review(id={self.id!r}, rating={self.rating!r})"


class UserMovie(db.Model):
    __tablename__ = "user_movie"
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id"), primary_key=True
    )
    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movie.id"), primary_key=True
    )
    # Note: No relationships needed here, as they are managed by 'User' and 'Movie'
