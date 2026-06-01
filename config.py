import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Базовая конфигурация приложения."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "helpdesk.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Папка для вложений к заявкам
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "app", "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 МБ на файл
