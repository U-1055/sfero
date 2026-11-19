"""Эндпоинты аутентификации"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from backend.app.extensions import db
from backend.app.models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    login = data.get("login")
    password = data.get("password")

    if not login or not password:
        return jsonify(error="Нужны login и password"), 400

    if User.query.filter_by(login=login).first():
        return jsonify(error="Такой логин уже занят"), 400

    user = User(login=login)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify(access_token=token, user_id=user.id), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    user = User.query.filter_by(login=data.get("login")).first()

    if not user or not user.check_password(data.get("password", "")):
        return jsonify(error="Неверный логин или пароль"), 401

    token = create_access_token(identity=str(user.id))
    return jsonify(access_token=token, user_id=user.id), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))
    return jsonify(id=user.id, login=user.login), 200

