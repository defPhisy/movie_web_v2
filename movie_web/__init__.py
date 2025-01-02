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
flask_secret_key = os.getenv("FLASK_SECRET_KEY")


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=flask_secret_key,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{DB_PATH}",
    )

    db_models.db.init_app(app)

    with app.app_context():
        db_models.db.create_all()

    app.register_blueprint(auth.bp)
    app.register_blueprint(blog.bp)
    app.add_url_rule("/", endpoint="index")

    error.register_error_handlers(app)

    # # run only once for dummy data population
    # with app.app_context():
    #     db_manager.populate_dummy_data()

    @app.context_processor
    def inject_fontawesome_key():
        return dict(fontawesome_key=font_awesome_key)

    return app
