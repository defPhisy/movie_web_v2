# Movie Web App

This Flask application allows users to manage their personal movie library. Users can add movies, update movie details, leave reviews, and manage their user profiles. The app fetches movie data from the OMDB API and supports login and user authentication.

## Features

- User Authentication: Secure login and session management.
- Movie Library: Users can add, update, delete, and view movies.
- Movie Details: View detailed information about movies fetched from the OMDB API.
- Movie Reviews: Users can add, update, and delete reviews for movies.
- Database Management: Uses SQLAlchemy for persistent data storage.

## Run App

#### navigate to the repository folder:

```shell
cd <repository-folder>
```

#### run flask app:

```shell
flask --app movie_web run --host 0.0.0.0
```
