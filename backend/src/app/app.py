from datetime import timedelta
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)  # Разрешаем запросы с фронтенда (React/Vue/HTML)

# Настройки базы данных (SQLite) и JWT
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///hackathon.db"
app.config["JWT_SECRET_KEY"] = "hackathon-super-secret-key"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=7)

db = SQLAlchemy(app)
jwt = JWTManager(app)


# 1. Таблица пользователей в БД
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)


# Автоматическое создание таблиц при старте
with app.app_context():
    db.create_all()


# 2. Регистрация
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    login = data.get("login")
    password = data.get("password")

    if not login or not password:
        return jsonify(error="Нужны login и password"), 400

    if User.query.filter_by(login=login).first():
        return jsonify(error="Такой логин уже занят"), 400

    new_user = User(login=login, password_hash=generate_password_hash(password))
    db.session.add(new_user)
    db.session.commit()

    # Сразу выдаем токен после регистрации
    token = create_access_token(identity=str(new_user.id))
    return jsonify(access_token=token, user_id=new_user.id), 201


# 3. Вход
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    user = User.query.filter_by(login=data.get("login")).first()

    if not user or not check_password_hash(user.password_hash, data.get("password", "")):
        return jsonify(error="Неверный логин или пароль"), 401

    token = create_access_token(identity=str(user.id))
    return jsonify(access_token=token, user_id=user.id), 200

# 4. Пример защищенного роута (проверка, что токен работает)


@app.route("/me", methods=["GET"])
@jwt_required()
def get_me():
    user_id = get_jwt_identity()  # Достаем ID пользователя из токена
    user = db.session.get(User, int(user_id))
    return jsonify(id=user.id, login=user.login), 200


if __name__ == "__main__":
    app.run(debug=True, port=5000)

