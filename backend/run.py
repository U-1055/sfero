from waitress import serve
from backend.app import create_app

app = create_app()

if __name__ == "__main__":
    host = app.config.get("HOST", "0.0.0.0")
    port = app.config.get("PORT", 5000)

    if app.config.get("DEBUG", False):
        app.run(debug=True, host=host, port=port)
    else:
        print(f"Сервер запущен в production-режиме на http://{host}:{port}")
        serve(app, host=host, port=port, threads=4)
