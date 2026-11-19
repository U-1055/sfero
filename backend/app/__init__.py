
from flask import Flask, jsonify
from backend.config import Config
from backend.app.extensions import db, jwt, cors


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app)

    from backend.app.api.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    # Сюда подключать новые блюпринты

    @app.route("/api/ping", methods=["GET"])
    def ping():
        return jsonify(status="ok"), 200

    from backend.app import models
    with app.app_context():
        db.create_all()

    return app
