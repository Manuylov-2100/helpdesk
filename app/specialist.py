"""Кабинет специалиста поддержки"""

from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.extensions import db
from app.models import (
    Ticket, Status, User, Comment, TicketHistory, KnowledgeArticle, Category,
)
from app.decorators import specialist_required

specialist_bp = Blueprint("specialist", __name__, url_prefix="/specialist")


@specialist_bp.route("/queue")
@login_required
@specialist_required
def queue():
    status_filter = request.args.get("status", "").strip()
    query = Ticket.query
    if status_filter:
        query = query.join(Status).filter(Status.name == status_filter)
    tickets = query.order_by(Ticket.created_at.desc()).all()
    statuses = Status.query.all()
    return render_template("specialist/queue.html",
                           tickets=tickets, statuses=statuses,
                           status_filter=status_filter)


@specialist_bp.route("/tickets/<int:ticket_id>", methods=["GET", "POST"])
@login_required
@specialist_required
def work(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    statuses = Status.query.all()
    specialists = User.query.join(User.role).filter(
        db.or_(
            User.role.has(name="Специалист поддержки"),
            User.role.has(name="Администратор"),
        )
    ).all()

    if request.method == "POST":
        action = request.form.get("action")

        if action == "status":
            new_status_id = int(request.form.get("status_id"))
            new_status = Status.query.get(new_status_id)
            old = ticket.status.name
            ticket.status_id = new_status_id
            if new_status.is_closed and ticket.closed_at is None:
                ticket.closed_at = datetime.utcnow()
            if not new_status.is_closed:
                ticket.closed_at = None
            db.session.add(TicketHistory(
                ticket_id=ticket.id, user_id=current_user.id,
                action="Смена статуса", old_value=old, new_value=new_status.name,
            ))
            db.session.commit()
            flash("Статус заявки обновлён.", "success")

        elif action == "assign":
            assignee_id = request.form.get("assignee_id") or None
            ticket.assignee_id = int(assignee_id) if assignee_id else None
            name = ticket.assignee.full_name if ticket.assignee else "—"
            db.session.add(TicketHistory(
                ticket_id=ticket.id, user_id=current_user.id,
                action="Назначение исполнителя", new_value=name,
            ))
            db.session.commit()
            flash("Исполнитель назначен.", "success")

        elif action == "comment":
            text = request.form.get("comment", "").strip()
            if text:
                db.session.add(Comment(ticket_id=ticket.id,
                                       author_id=current_user.id, text=text))
                db.session.commit()
                flash("Комментарий добавлен.", "success")

        return redirect(url_for("specialist.work", ticket_id=ticket.id))

    return render_template("specialist/work.html", ticket=ticket,
                           statuses=statuses, specialists=specialists)


@specialist_bp.route("/knowledge")
@login_required
@specialist_required
def knowledge_list():
    articles = KnowledgeArticle.query.order_by(KnowledgeArticle.updated_at.desc()).all()
    return render_template("specialist/knowledge_list.html", articles=articles)


@specialist_bp.route("/knowledge/new", methods=["GET", "POST"])
@specialist_bp.route("/knowledge/<int:article_id>/edit", methods=["GET", "POST"])
@login_required
@specialist_required
def knowledge_edit(article_id=None):
    article = KnowledgeArticle.query.get_or_404(article_id) if article_id else None
    categories = Category.query.all()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        category_id = request.form.get("category_id") or None
        is_published = bool(request.form.get("is_published"))

        if not title or not content:
            flash("Заполните заголовок и текст статьи.", "error")
        else:
            if article is None:
                article = KnowledgeArticle(author_id=current_user.id)
                db.session.add(article)
            article.title = title
            article.content = content
            article.category_id = int(category_id) if category_id else None
            article.is_published = is_published
            db.session.commit()
            flash("Статья сохранена.", "success")
            return redirect(url_for("specialist.knowledge_list"))

    return render_template("specialist/knowledge_edit.html",
                           article=article, categories=categories)


@specialist_bp.route("/stats")
@login_required
@specialist_required
def stats():
    total = Ticket.query.count()
    assigned = Ticket.query.filter_by(assignee_id=current_user.id).count()
    closed = Ticket.query.join(Status).filter(Status.is_closed.is_(True)).count()
    open_count = total - closed
    by_status = (
        db.session.query(Status.name, db.func.count(Ticket.id))
        .outerjoin(Ticket).group_by(Status.name).all()
    )
    return render_template("specialist/stats.html",
                           total=total, assigned=assigned, closed=closed,
                           open_count=open_count, by_status=by_status)
