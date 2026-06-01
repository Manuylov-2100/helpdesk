# Служба технической поддержки университета

Веб-сервис автоматизации процесса обработки заявок в службу технической поддержки университета.

Сайт разработан на стеке: Python 3, Flask, SQLAlchemy, SQLite, Jinja2, python-docx, openpyxl.

## Установка и запуск локально

```bash
python -m venv venv
# Windows: venv\Scripts\activate | Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
python seed.py
python run.py
```
Приложение будет доступно по адресу http://127.0.0.1:5000

## Учётные записи (после запуска)

| Логин      | Пароль  | Роль                 |
|------------|---------|----------------------|
| admin      | admin123| Администратор        |
| specialist | spec123 | Специалист поддержки |
| user       | user123 | Пользователь         |

## Структура проекта

```
helpdesk/
├── app/
│   ├── __init__.py        # фабрика приложения create_app()
│   ├── extensions.py      # экземпляры db и login_manager
│   ├── models.py          # 13 моделей данных
│   ├── templates/         # HTML-шаблоны
│   ├── static/            # CSS, изображения
│   └── uploads/           # вложения к заявкам
├── config.py              # конфигурация
├── run.py                 # точка входа
├── seed.py                # наполнение БД тестовыми данными
└── requirements.txt
```

## Модель данных (13 таблиц)

Role, User, Department, Category, Priority, Status, Ticket, Comment,
Attachment, Equipment, KnowledgeArticle, TicketHistory, Feedback.
