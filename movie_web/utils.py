def calculate_imdb_stars(rating):
    """Converts a 0-10 rating to full, half, and empty stars on a 0-5 scale."""
    converted_rating = round(rating / 2, 1)
    full_stars = int(converted_rating)
    half_star = 1 if converted_rating - full_stars >= 0.5 else 0
    empty_stars = 5 - full_stars - half_star
    return {"full": full_stars, "half": half_star, "empty": empty_stars}