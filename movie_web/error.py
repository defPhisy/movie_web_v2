from flask import render_template

ERROR_MESSAGES = {
    400: "Oops! It looks like something went wrong with your request. Please try again.",
    401: "You need to log in to access this page. Please authenticate and try again.",
    403: "Sorry, you don't have permission to view this page.",
    404: "The page you're looking for doesn't exist. Check the URL or go back to the homepage.",
    405: "It seems like you're trying to access this page with the wrong method. Please try again using the correct action.",
    500: "Our server ran into a problem. Please try again later or contact support.",
    "default": "An unexpected error occurred. Please try again or contact support.",
}


def register_error_handlers(app):
    # Register handlers for each error code
    for code in ERROR_MESSAGES:
        if isinstance(code, int):  # Only register numeric HTTP codes
            app.register_error_handler(code, render_error_page)

    # Register a fallback for generic exceptions
    app.register_error_handler(Exception, render_error_page)


def render_error_page(e):
    """Generic error page renderer."""
    print("RENDER ERROR PAGE")
    code = getattr(e, "code", 500)
    error_msg = ERROR_MESSAGES.get(code, ERROR_MESSAGES["default"])
    return render_template(
        "error/error.html", error_code=code, error_msg=error_msg
    ), code
