"""Наполнение базы данных тестовыми данными"""

from datetime import datetime, timedelta

from app import create_app
from app.extensions import db
from app.models import (
    Role, Department, User, Category, Priority, Status,
    Equipment, Ticket, Comment, Attachment, KnowledgeArticle,
    TicketHistory, Feedback,
)


def seed():
    app = create_app()
    with app.app_context():
        # Очистка для повторного запуска
        db.drop_all()
        db.create_all()

        #  Роли 
        r_admin = Role(name="Администратор", description="Полный доступ к системе")
        r_spec = Role(name="Специалист поддержки", description="Обработка заявок")
        r_user = Role(name="Пользователь", description="Создание заявок")
        db.session.add_all([r_admin, r_spec, r_user])
        db.session.flush()

        #   Подразделения  
        dep_it = Department(name="Департамент информационных технологий",
                            description="Обслуживание ИТ-инфраструктуры")
        dep_edu = Department(name="Учебный отдел", description="Организация учебного процесса")
        dep_acc = Department(name="Бухгалтерия", description="Финансовый учёт")
        db.session.add_all([dep_it, dep_edu, dep_acc])
        db.session.flush()

        #   Пользователи 
        admin = User(username="admin", email="admin@muiv.ru",
                     full_name="Администратор Системы",
                     role=r_admin, department=dep_it)
        admin.set_password("admin123")

        spec = User(username="specialist", email="support@muiv.ru",
                    full_name="Иванов Иван Иванович",
                    role=r_spec, department=dep_it)
        spec.set_password("spec123")

        user = User(username="user", email="user@muiv.ru",
                    full_name="Петров Пётр Петрович",
                    role=r_user, department=dep_edu)
        user.set_password("user123")

        db.session.add_all([admin, spec, user])
        db.session.flush()

        #   Справочники заявок  
        categories = [
            Category(name="Сетевое оборудование", description="Проблемы с сетью и доступом"),
            Category(name="Программное обеспечение", description="Установка и настройка ПО"),
            Category(name="Оргтехника", description="Принтеры, МФУ, сканеры"),
            Category(name="Учётные записи", description="Доступ и пароли"),
        ]
        priorities = [
            Priority(name="Низкий", level=1),
            Priority(name="Средний", level=2),
            Priority(name="Высокий", level=3),
            Priority(name="Критический", level=4),
        ]
        statuses = [
            Status(name="Новая", is_closed=False),
            Status(name="В работе", is_closed=False),
            Status(name="Ожидает ответа", is_closed=False),
            Status(name="Решена", is_closed=True),
            Status(name="Отклонена", is_closed=True),
        ]
        db.session.add_all(categories + priorities + statuses)
        db.session.flush()

        #   Оборудование  
        equipment = [
            Equipment(inventory_number="ПК-001", name="Системный блок HP",
                      type="Компьютер", department=dep_edu),
            Equipment(inventory_number="ПР-014", name="Принтер Kyocera",
                      type="Принтер", department=dep_acc),
            Equipment(inventory_number="СВ-003", name="Коммутатор Cisco",
                      type="Сетевое оборудование", department=dep_it),
        ]
        db.session.add_all(equipment)
        db.session.flush()

        #   Заявки  
        t1 = Ticket(number="2026-0001", title="Не работает доступ в интернет",
                    description="В аудитории 305 пропал доступ к сети.",
                    author=user, assignee=spec,
                    category=categories[0], priority=priorities[2],
                    status=statuses[1], equipment=equipment[2],
                    created_at=datetime.utcnow() - timedelta(days=3))
        t2 = Ticket(number="2026-0002", title="Установить пакет MS Office",
                    description="Требуется установить офисный пакет на новый ПК.",
                    author=user, category=categories[1], priority=priorities[1],
                    status=statuses[0],
                    created_at=datetime.utcnow() - timedelta(days=1))
        t3 = Ticket(number="2026-0003", title="Замятие бумаги в принтере",
                    description="Принтер ПР-014 постоянно зажёвывает бумагу.",
                    author=user, assignee=spec,
                    category=categories[2], priority=priorities[0],
                    status=statuses[3], equipment=equipment[1],
                    created_at=datetime.utcnow() - timedelta(days=7),
                    closed_at=datetime.utcnow() - timedelta(days=5))
        db.session.add_all([t1, t2, t3])
        db.session.flush()

        #   Комментарии, история, вложения  
        db.session.add_all([
            Comment(ticket=t1, author=spec, text="Выехал на место, проверяю коммутатор."),
            Comment(ticket=t3, author=spec, text="Извлёк замятую бумагу, заявка решена."),
            TicketHistory(ticket=t1, user_id=spec.id, action="Смена статуса",
                          old_value="Новая", new_value="В работе"),
            TicketHistory(ticket=t3, user_id=spec.id, action="Смена статуса",
                          old_value="В работе", new_value="Решена"),
            Attachment(ticket=t1, filename="screenshot.png",
                       filepath="uploads/screenshot.png", uploaded_by=user.id),
        ])

        #   База знаний  
        db.session.add_all([
            KnowledgeArticle(title="Как сбросить пароль учётной записи",
                             content="Пошаговая инструкция по сбросу пароля...",
                             category=categories[3], author_id=spec.id),
            KnowledgeArticle(title="Подключение к корпоративной сети Wi-Fi",
                             content="Настройки подключения к сети университета...",
                             category=categories[0], author_id=spec.id),
        ])

        #   Обратная связь  
        db.session.add_all([
            Feedback(user_name="Петров Пётр Петрович", email="user@muiv.ru",
                     rating=5, message="Заявка решена быстро, спасибо!", ticket=t3),
            Feedback(user_name="Гость", email="guest@example.com",
                     message="Удобный сервис, хотелось бы мобильное приложение."),
        ])

        db.session.commit()

        #   Итоговая статистика  
        print("База данных наполнена тестовыми данными.")
        print(f"  Ролей:          {Role.query.count()}")
        print(f"  Подразделений:  {Department.query.count()}")
        print(f"  Пользователей:  {User.query.count()}")
        print(f"  Категорий:      {Category.query.count()}")
        print(f"  Приоритетов:    {Priority.query.count()}")
        print(f"  Статусов:       {Status.query.count()}")
        print(f"  Оборудования:   {Equipment.query.count()}")
        print(f"  Заявок:         {Ticket.query.count()}")
        print(f"  Комментариев:   {Comment.query.count()}")
        print(f"  Вложений:       {Attachment.query.count()}")
        print(f"  Статей БЗ:      {KnowledgeArticle.query.count()}")
        print(f"  Записей истории:{TicketHistory.query.count()}")
        print(f"  Отзывов:        {Feedback.query.count()}")
        print("\nУчётные записи:")
        print("  admin / admin123        — Администратор")
        print("  specialist / spec123    — Специалист поддержки")
        print("  user / user123          — Заявитель")


if __name__ == "__main__":
    seed()
