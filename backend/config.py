import os
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv

# Подгружаем переменные из .env, если файл существует
load_dotenv()

# Вычисляем путь к папке backend/, чтобы база всегда создавалась в одном месте
BASE_DIR = Path(__file__).resolve().parent


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "hackathon-dev-secret-key")

    # База данных SQLite (по умолчанию создаст файл backend/hackathon.db)
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'hackathon.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Настройки JWT-токенов
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "hackathon-jwt-secret-key")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)
