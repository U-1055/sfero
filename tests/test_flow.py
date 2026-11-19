"""Общий тест"""
import uuid
import requests

BASE_URL = "http://localhost:5000/api"


def run_smoke_test():
    print("🚀 Запуск Smoke-теста API...")

    # 1. Проверка доступности сервера (/api/ping)
    ping_resp = requests.get(f"{BASE_URL}/ping", timeout=5)
    assert ping_resp.status_code == 200, f"Сервер не отвечает: {ping_resp.status_code}"
    assert ping_resp.json().get("status") == "ok"
    print("Сервер доступен (/api/ping)")

    # Генерируем уникальный логин, чтобы тест можно было запускать много раз подряд
    unique_login = f"test_user_{uuid.uuid4().hex[:6]}"
    creds = {"login": unique_login, "password": "secret_password_123"}

    # 2. Проверка регистрации (/api/auth/register)
    reg_resp = requests.post(f"{BASE_URL}/auth/register", json=creds, timeout=5)
    assert reg_resp.status_code == 201, f"Ошибка регистрации: {reg_resp.text}"
    print(f"Регистрация работает (создан {unique_login})")

    # 3. Проверка входа и получения JWT-токена (/api/auth/login)
    login_resp = requests.post(f"{BASE_URL}/auth/login", json=creds, timeout=5)
    assert login_resp.status_code == 200, f"Ошибка входа: {login_resp.text}"
    token = login_resp.json().get("access_token")
    assert token, "В ответе не пришел access_token"
    print("Вход и выдача токена работают")

    # 4. Проверка защищенного роута (/api/auth/me)
    headers = {"Authorization": f"Bearer {token}"}
    me_resp = requests.get(f"{BASE_URL}/auth/me", headers=headers, timeout=5)
    assert me_resp.status_code == 200, f"Ошибка доступа по токену: {me_resp.text}"
    assert me_resp.json().get("login") == unique_login
    print("Защищенный маршрут (/api/auth/me) работает")

    print("Все базовые проверки успешно пройдены!")


if __name__ == "__main__":
    try:
        run_smoke_test()
    except requests.ConnectionError:
        print("Ошибка: не удалось подключиться к серверу. Сначала запусти python run.py!")
    except AssertionError as e:
        print(f"Тест провален: {e}")
