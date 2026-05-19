import os
from threading import Thread
from flask import Flask

app = Flask("")

@app.route("/")
def home():
    return "Bot is running!"

def run():
    # Используем порт из переменных окружения (Render передаст его), или 8080 по умолчанию
    port = int(os.environ.get("PORT", 8080))
    # Запускаем Flask-сервер так, чтобы он слушал на 0.0.0.0
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    """Запускает Flask в отдельном фоновом потоке."""
    t = Thread(target=run)
    # daemon=True означает, что поток закроется при остановке основного процесса бота
    t.daemon = True
    t.start()
