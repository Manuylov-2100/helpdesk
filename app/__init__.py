import os

from flask import Flask, render_template

from config import Config
from app.extensions import db, login_manager


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Папка для вложений
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Инициализация расширений
    db.init_app(app)
    login_manager.init_app(app)

    # Модели импортируются, чтобы они были зарегистрированы в метаданных
    from app import models

    @app.route("/")
    def index():
        return render_template("index.html")

    # Создание таблиц при запуске
    with app.app_context():
        db.create_all()

    return app
