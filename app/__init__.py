import os
from datetime import datetime

from flask import Flask, render_template

from config import Config
from app.extensions import db, login_manager


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    from app import models

    # Регистрация blueprints
    from app.main import main_bp
    from app.auth import auth_bp
    from app.tickets import tickets_bp
    from app.specialist import specialist_bp
    from app.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(tickets_bp)
    app.register_blueprint(specialist_bp)
    app.register_blueprint(admin_bp)


    @app.context_processor
    def inject_now():
        return {"current_year": datetime.utcnow().year}

    # Обработчики ошибок
    @app.errorhandler(401)
    def unauthorized(e):
        return render_template("errors/error.html", code=401,
                               message="Требуется авторизация."), 401

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/error.html", code=403,
                               message="Доступ запрещён."), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/error.html", code=404,
                               message="Страница не найдена."), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/error.html", code=500,
                               message="Внутренняя ошибка сервера."), 500

    with app.app_context():
        db.create_all()

    return app
