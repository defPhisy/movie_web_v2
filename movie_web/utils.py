def calculate_imdb_stars(rating: float) -> dict[str, int]:
    """
    Converts a 0-10 IMDb rating to a 0-5 star rating, breaking it into full, half, and empty stars.

    :param rating: A numeric IMDb rating on a scale of 0 to 10.
    :type rating: float

    :return: A dictionary containing the count of full, half, and empty stars.
    :rtype: dict(str, int)

    :example:

    >>> calculate_imdb_stars(7.5)
    {'full': 3, 'half': 1, 'empty': 1}
    """
    """Converts a 0-10 rating to full, half, and empty stars on a 0-5 scale."""
    converted_rating = round(rating / 2, 1)
    full_stars = int(converted_rating)
    half_star = 1 if converted_rating - full_stars >= 0.5 else 0
    empty_stars = 5 - full_stars - half_star
    return {"full": full_stars, "half": half_star, "empty": empty_stars}
