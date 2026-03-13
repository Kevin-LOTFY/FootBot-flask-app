import os
from flask import Flask
from core.config import Config
from core.extensions import db
from core.routes import main_bp
from core.seed_data import init_db_with_seed


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    app.register_blueprint(main_bp)

    with app.app_context():
        init_db_with_seed()

    return app


app = create_app()


if __name__ == '__main__':
    app.run(debug=True)
