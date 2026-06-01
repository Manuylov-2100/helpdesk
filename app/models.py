"""Модели данных приложения. 13 таблиц:
    Role, User, Department, Category, Priority, Status, Ticket, Comment, Attachment, Equipment, KnowledgeArticle, TicketHistory, Feedback
"""

from datetime import datetime

from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

from app.extensions import db, login_manager


#  Справочники и пользователи
class Role(db.Model):
    """Роль пользователя (администратор, специалист, заявитель)."""

    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))

    users = db.relationship("User", back_populates="role")

    def __repr__(self):
        return f"<Role {self.name}>"


class Department(db.Model):
    """Структурное подразделение университета."""

    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(255))

    users = db.relationship("User", back_populates="department")
    equipment = db.relationship("Equipment", back_populates="department")

    def __repr__(self):
        return f"<Department {self.name}>"


class User(UserMixin, db.Model):
    """Пользователь системы."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))

    role = db.relationship("Role", back_populates="users")
    department = db.relationship("Department", back_populates="users")

    authored_tickets = db.relationship(
        "Ticket", back_populates="author", foreign_keys="Ticket.author_id"
    )
    assigned_tickets = db.relationship(
        "Ticket", back_populates="assignee", foreign_keys="Ticket.assignee_id"
    )
    comments = db.relationship("Comment", back_populates="author")

    #  работа с паролем
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role is not None and self.role.name == "Администратор"

    @property
    def is_specialist(self):
        return self.role is not None and self.role.name == "Специалист поддержки"

    def __repr__(self):
        return f"<User {self.username}>"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

#  Справочники заявок
class Category(db.Model):
    """Категория заявки (например, «Сеть», «Программное обеспечение»)."""

    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))

    tickets = db.relationship("Ticket", back_populates="category")
    articles = db.relationship("KnowledgeArticle", back_populates="category")

    def __repr__(self):
        return f"<Category {self.name}>"


class Priority(db.Model):
    """Приоритет заявки."""

    __tablename__ = "priorities"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    level = db.Column(db.Integer, default=0)  # чем выше, тем приоритетнее
    description = db.Column(db.String(255))

    tickets = db.relationship("Ticket", back_populates="priority")

    def __repr__(self):
        return f"<Priority {self.name}>"


class Status(db.Model):
    """Статус заявки."""

    __tablename__ = "statuses"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    is_closed = db.Column(db.Boolean, default=False)
    description = db.Column(db.String(255))

    tickets = db.relationship("Ticket", back_populates="status")

    def __repr__(self):
        return f"<Status {self.name}>"


#  Оборудование
class Equipment(db.Model):
    """Единица учитываемого оборудования."""

    __tablename__ = "equipment"

    id = db.Column(db.Integer, primary_key=True)
    inventory_number = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    type = db.Column(db.String(100))
    status = db.Column(db.String(50), default="В эксплуатации")

    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    department = db.relationship("Department", back_populates="equipment")

    tickets = db.relationship("Ticket", back_populates="equipment")

    def __repr__(self):
        return f"<Equipment {self.inventory_number}>"


#  Заявки и связанные сущности
class Ticket(db.Model):
    """Заявка в службу технической поддержки."""

    __tablename__ = "tickets"

    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at = db.Column(db.DateTime)

    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    assignee_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    priority_id = db.Column(db.Integer, db.ForeignKey("priorities.id"), nullable=False)
    status_id = db.Column(db.Integer, db.ForeignKey("statuses.id"), nullable=False)
    equipment_id = db.Column(db.Integer, db.ForeignKey("equipment.id"))

    author = db.relationship(
        "User", back_populates="authored_tickets", foreign_keys=[author_id]
    )
    assignee = db.relationship(
        "User", back_populates="assigned_tickets", foreign_keys=[assignee_id]
    )
    category = db.relationship("Category", back_populates="tickets")
    priority = db.relationship("Priority", back_populates="tickets")
    status = db.relationship("Status", back_populates="tickets")
    equipment = db.relationship("Equipment", back_populates="tickets")

    comments = db.relationship(
        "Comment", back_populates="ticket", cascade="all, delete-orphan"
    )
    attachments = db.relationship(
        "Attachment", back_populates="ticket", cascade="all, delete-orphan"
    )
    history = db.relationship(
        "TicketHistory", back_populates="ticket", cascade="all, delete-orphan"
    )
    feedback = db.relationship("Feedback", back_populates="ticket")

    def __repr__(self):
        return f"<Ticket {self.number}>"


class Comment(db.Model):
    """Комментарий к заявке."""

    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    ticket = db.relationship("Ticket", back_populates="comments")
    author = db.relationship("User", back_populates="comments")

    def __repr__(self):
        return f"<Comment {self.id} for Ticket {self.ticket_id}>"


class Attachment(db.Model):
    """Вложение к заявке (скриншот, файл)."""

    __tablename__ = "attachments"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey("users.id"))

    ticket = db.relationship("Ticket", back_populates="attachments")

    def __repr__(self):
        return f"<Attachment {self.filename}>"


class KnowledgeArticle(db.Model):
    """Статья базы знаний."""

    __tablename__ = "knowledge_articles"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    category = db.relationship("Category", back_populates="articles")

    def __repr__(self):
        return f"<KnowledgeArticle {self.title}>"


class TicketHistory(db.Model):
    """История изменений заявки (журнал действий)."""

    __tablename__ = "ticket_history"

    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(100), nullable=False)
    old_value = db.Column(db.String(255))
    new_value = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    ticket = db.relationship("Ticket", back_populates="history")

    def __repr__(self):
        return f"<TicketHistory {self.action} for Ticket {self.ticket_id}>"


class Feedback(db.Model):
    """Обратная связь и оценка качества обслуживания."""

    __tablename__ = "feedback"

    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(150))
    email = db.Column(db.String(120))
    rating = db.Column(db.Integer)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"))
    ticket = db.relationship("Ticket", back_populates="feedback")

    def __repr__(self):
        return f"<Feedback {self.id}>"
