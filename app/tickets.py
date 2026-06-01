"""Личный кабинет заявителя"""

import os
from datetime import datetime

from flask import (
    Blueprint, render_template, redirect, url_for, flash, request,
    current_app, send_from_directory, abort,
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import (
    Ticket, Category, Priority, Status, Comment, Attachment, TicketHistory,
)

tickets_bp = Blueprint("tickets", __name__, url_prefix="/cabinet")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf", "txt", "log", "doc", "docx"}


def _allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _generate_number():
    year = datetime.utcnow().year
    count = Ticket.query.count() + 1
    return f"{year}-{count:04d}"


@tickets_bp.route("/tickets")
@login_required
def my_tickets():
    page = request.args.get("page", 1, type=int)
    pagination = (
        Ticket.query.filter_by(author_id=current_user.id)
        .order_by(Ticket.created_at.desc())
        .paginate(page=page, per_page=10, error_out=False)
    )
    return render_template("cabinet/my_tickets.html", pagination=pagination)


@tickets_bp.route("/tickets/new", methods=["GET", "POST"])
@login_required
def new_ticket():
    categories = Category.query.all()
    priorities = Priority.query.order_by(Priority.level).all()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category_id = request.form.get("category_id")
        priority_id = request.form.get("priority_id")

        if not title or not description or not category_id or not priority_id:
            flash("Заполните все обязательные поля.", "error")
        else:
            status = Status.query.filter_by(name="Новая").first()
            ticket = Ticket(
                number=_generate_number(), title=title, description=description,
                author_id=current_user.id, category_id=int(category_id),
                priority_id=int(priority_id), status_id=status.id,
            )
            db.session.add(ticket)
            db.session.flush()

            db.session.add(TicketHistory(
                ticket_id=ticket.id, user_id=current_user.id,
                action="Создание заявки", new_value="Новая",
            ))

            # Загрузка вложения
            file = request.files.get("attachment")
            if file and file.filename:
                if _allowed_file(file.filename):
                    fname = secure_filename(f"{ticket.number}_{file.filename}")
                    path = os.path.join(current_app.config["UPLOAD_FOLDER"], fname)
                    file.save(path)
                    db.session.add(Attachment(
                        ticket_id=ticket.id, filename=file.filename,
                        filepath=fname, uploaded_by=current_user.id,
                    ))
                else:
                    flash("Недопустимый формат вложения — заявка создана без файла.", "error")

            db.session.commit()
            flash(f"Заявка {ticket.number} создана.", "success")
            return redirect(url_for("tickets.view_ticket", ticket_id=ticket.id))

    return render_template("cabinet/new_ticket.html",
                           categories=categories, priorities=priorities)


@tickets_bp.route("/tickets/<int:ticket_id>", methods=["GET", "POST"])
@login_required
def view_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    
    if ticket.author_id != current_user.id and not (
        current_user.is_admin or current_user.is_specialist
    ):
        abort(403)

    if request.method == "POST":
        text = request.form.get("comment", "").strip()
        if text:
            db.session.add(Comment(ticket_id=ticket.id,
                                   author_id=current_user.id, text=text))
            db.session.commit()
            flash("Комментарий добавлен.", "success")
        return redirect(url_for("tickets.view_ticket", ticket_id=ticket.id))

    return render_template("cabinet/view_ticket.html", ticket=ticket)


@tickets_bp.route("/uploads/<path:filename>")
@login_required
def download_attachment(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)


@tickets_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        if full_name:
            current_user.full_name = full_name
        if email and "@" in email:
            current_user.email = email
        db.session.commit()
        flash("Профиль обновлён.", "success")
        return redirect(url_for("tickets.profile"))
    return render_template("cabinet/profile.html")


@tickets_bp.route("/notifications")
@login_required
def notifications():
    
    ticket_ids = [t.id for t in current_user.authored_tickets]
    items = (
        TicketHistory.query.filter(TicketHistory.ticket_id.in_(ticket_ids))
        .order_by(TicketHistory.created_at.desc())
        .limit(20)
        .all()
        if ticket_ids else []
    )
    return render_template("cabinet/notifications.html", items=items)
