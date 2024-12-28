"""
Module for fetching movie data from the OMDB API.

This module loads the API key from environment variables and provides a function
to request movie information with retry logic for handling HTTP errors.

Usage:
    Call `request_for_movie(title: str)` with a movie title.
"""

import os

import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

load_dotenv()
API_KEY = os.getenv("OMDB_API_KEY")


def get_movie(title=None, year=None, imdb_id=None) -> dict:
    """
    Send a GET request with a movie title and/or year or an imdb-ID to www.omdbapi.com with authorization
    and retry logic.

    Args:
        title (str): The movie to search for.

    Returns:
        dict: The JSON response from the server.

    Raises:
        HTTPError: If an HTTP error occurs and retries are exhausted.
        Timeout: If the request times out and retries are exhausted.
    """

    url = "http://www.omdbapi.com/?"
    headers = {"Content-Type": "application/json"}
    params = set_params(title, year, imdb_id)
    timeout = 5

    # Configure retries with exponential backoff
    retries = Retry(
        total=3,  # Total number of retries
        backoff_factor=1,  # Wait time between retries: 1 second, 2 seconds, 4 seconds
        status_forcelist=[
            429,
            500,
            502,
            503,
            504,
        ],  # Retry on specific status codes
    )

    # Set up the HTTPAdapter with retry configuration
    adapter = HTTPAdapter(max_retries=retries)

    # Use requests.Session() to apply retries
    with requests.Session() as session:
        session.mount("https://", adapter)
        response = session.get(
            url, headers=headers, params=params, timeout=timeout
        )
        response.raise_for_status()  # Raise an error for bad HTTP responses
        return response.json()


def set_params(title, year, imdb_id):
    if not title and not imdb_id:
        raise ValueError("Need at least a movie title or an imdb-ID")

    params = {}
    if title:
        params.update({"t": title})
    if year:
        params.update({"y": year})
    if imdb_id:
        params = {"i": imdb_id}

    params.update({
        "apikey": API_KEY,
        "plot": "full",  # "full" or "short" movie description
    })

    return params


def test_api_requests():
    dark_knight_response = {
        "Title": "The Dark Knight",
        "Year": "2008",
        "Rated": "PG-13",
        "Released": "18 Jul 2008",
        "Runtime": "152 min",
        "Genre": "Action, Crime, Drama",
        "Director": "Christopher Nolan",
        "Writer": "Jonathan Nolan, Christopher Nolan, David S. Goyer",
        "Actors": "Christian Bale, Heath Ledger, Aaron Eckhart",
        "Plot": "When a menace known as the Joker wreaks havoc and chaos on the people of Gotham, Batman, James Gordon and Harvey Dent must work together to put an end to the madness.",
        "Language": "English, Mandarin",
        "Country": "United States, United Kingdom",
        "Awards": "Won 2 Oscars. 164 wins & 164 nominations total",
        "Poster": "https://m.media-amazon.com/images/M/MV5BMTMxNTMwODM0NF5BMl5BanBnXkFtZTcwODAyMTk2Mw@@._V1_SX300.jpg",
        "Ratings": [
            {"Source": "Internet Movie Database", "Value": "9.0/10"},
            {"Source": "Rotten Tomatoes", "Value": "94%"},
            {"Source": "Metacritic", "Value": "84/100"},
        ],
        "Metascore": "84",
        "imdbRating": "9.0",
        "imdbVotes": "2,947,373",
        "imdbID": "tt0468569",
        "Type": "movie",
        "DVD": "N/A",
        "BoxOffice": "$534,987,076",
        "Production": "N/A",
        "Website": "N/A",
        "Response": "True",
    }

    movie_not_found = {"Response": "False", "Error": "Movie not found!"}

    assert get_movie("The Dark Knight") == dark_knight_response
    assert get_movie("Dune Part 1") == movie_not_found
