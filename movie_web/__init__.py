import os

from dotenv import load_dotenv
from flask import Flask

from . import auth, blog, db_models, error

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
DB_FOLDER = "./data"
DB_NAME = "movie_web.sqlite"
DB_PATH = os.path.join(ROOT_PATH, DB_FOLDER, DB_NAME)


load_dotenv()
font_awesome_key = os.getenv("FONT_AWESOME_KEY")


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{DB_PATH}",
    )

    # if test_config is None:
    #     # load the instance config, if it exists, when not testing
    #     app.config.from_pyfile("config.py", silent=True)
    # else:
    #     # load the test config if passed in
    #     app.config.from_mapping(test_config)

    # # ensure the instance folder exists
    # try:
    #     os.makedirs(app.instance_path)
    # except OSError:
    #     pass

    db_models.db.init_app(app)

    with app.app_context():
        db_models.db.create_all()

    app.register_blueprint(auth.bp)
    app.register_blueprint(blog.bp)
    app.add_url_rule("/", endpoint="index")

    error.register_error_handlers(app)

    @app.context_processor
    def inject_fontawesome_key():
        return dict(fontawesome_key=font_awesome_key)

    return app
