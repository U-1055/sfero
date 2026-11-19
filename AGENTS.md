# AGENTS.md — Инструкции для ИИ-ассистентов

Этот файл содержит правила архитектуры, стека и стиля кода для этого репозитория. Строго соблюдай их при генерации и редактировании любого кода.

## 1. Стек технологий
* **Backend:** Python 3.12, Flask, Flask-SQLAlchemy (SQLite), Waitress.
* **Frontend:** Streamlit, `requests` (никакого React/Vue/HTML+JS).
* **Инфраструктура:** встроенный модуль `logging`, pathlib - для работы с файлами.

## 2. Структура проекта и границы слоев
```text
project-root/
├── backend/
│   ├── app/
│   │   ├── api/            # Flask Blueprints (тонкие HTTP-роуты)
│   │   ├── extensions.py   # Непривязанные экземпляры db, jwt, cors
│   │   ├── integrations.py # Запросы к внешним API (нейросети, парсеры)
│   │   ├── run.py         # Фабрика приложения create_app() и настройка logging
│   │   ├── models.py       # SQLAlchemy-модели таблиц
│   │   └── services.py     # Бизнес-логика и ML-инференс (чистые функции)
│   └── config.py           # Класс Config (переменные окружения из .env)
├── frontend/
│   ├── api_client.py       # HTTP-клиент для запросов к Flask
│   └── app.py              # UI на Streamlit
├── tests/
│   └── test_flow.py        # Сквозные smoke-тесты через requests
└── run.py                  # Точка входа бэкенда (Flask dev / Waitress prod)
```

## 3. Строгие архитектурные правила

### Импорты и пути
* Использовать **только абсолютные импорты** от корня репозитория (например: `from backend.app.extensions import db`, `from backend.app.models import User`). Относительные импорты (`from ..models`) запрещены.
* В начале `frontend/app.py` сохранять добавление корня проекта в `sys.path`.

### Backend (`backend/`)
* **Роуты (`backend/app/api/*.py`):**
  * Группируются по бизнес-сущностям в отдельных `Blueprint`.
  * Каждый новый `Blueprint` обязательно регистрируется в `backend/app/main.py` внутри `create_app()` с префиксом `/api/`.
  * Роут должен быть тонким: достать JSON (`request.get_json(silent=True) or {}`), проверить обязательные поля, вызвать функцию из `services.py` (или выполнить простой CRUD) и вернуть `jsonify(...)` с корректным HTTP-статусом.
* **Бизнес-логика (`backend/app/services.py`):**
  * Писать **только обычными функциями**, не оборачивать в классы-сервисы.
  * Запрещено импортировать `flask.request` или `flask.jsonify` внутри `services.py`.
* **Внешние API (`backend/app/integrations.py`):**
  * Все запросы к сторонним сервисам изолировать здесь.
  * Обязательно указывать `timeout` (5–15 сек) в `requests` и оборачивать вызов в `try...except requests.RequestException` с безопасным fallback-ответом.
* **База данных (`backend/app/models.py`):**
  * Все таблицы описывать в одном файле `models.py`.
  * Внутри моделей разрешены только методы работы с полями (`set_password`, `check_password`) и сериализации (`to_dict`). Не вызывать `db.session.commit()` внутри методов модели.
* **Конфигурация и логи:**
  * Никогда не хардкодить секретные ключи — читать через `os.getenv` в `backend/config.py`.
  * Вместо `print()` использовать стандартный логгер: `logger = logging.getLogger(__name__)`.

### Frontend (`frontend/`)
* Фронтенд **не обращается** к SQLite или внешним API напрямую — только через HTTP-запросы к бэкенду.
* Все вызовы `requests` выносить в `frontend/api_client.py`, используя `BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5000/api")`.
* JWT-токен хранить в `st.session_state["token"]` и передавать в заголовке `Authorization: Bearer <token>`.

## 4. Команды запуска и проверки
* **Запуск бэкенда:** `python run.py` (режим управляется переменной `FLASK_DEBUG` в `.env`).
* **Запуск фронтенда:** `streamlit run frontend/app.py`
* **Запуск в Docker:** `docker compose up --build`
* **Smoke-тест API:** `python -m tests.test_flow` (при запущенном бэкенде).
