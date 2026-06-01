"""Админ-панель"""

from datetime import datetime

from flask import (
    Blueprint, render_template, redirect, url_for, flash, request, send_file,
)
from flask_login import login_required

from app.extensions import db
from app.models import (
    User, Role, Department, Category, Priority, Status, Equipment,
    Ticket, KnowledgeArticle, Feedback,
)
from app.decorators import admin_required
from app.documents import generate_act_docx, generate_report_xlsx

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    stats = {
        "users": User.query.count(),
        "tickets": Ticket.query.count(),
        "open": Ticket.query.join(Status).filter(Status.is_closed.is_(False)).count(),
        "equipment": Equipment.query.count(),
        "articles": KnowledgeArticle.query.count(),
        "feedback": Feedback.query.count(),
    }
    return render_template("admin/dashboard.html", stats=stats)


#  Пользователи  #
@admin_bp.route("/users")
@login_required
@admin_required
def users():
    all_users = User.query.order_by(User.id).all()
    roles = Role.query.all()
    return render_template("admin/users.html", users=all_users, roles=roles)


@admin_bp.route("/users/<int:user_id>/role", methods=["POST"])
@login_required
@admin_required
def change_role(user_id):
    user = User.query.get_or_404(user_id)
    role_id = request.form.get("role_id")
    if role_id:
        user.role_id = int(role_id)
        db.session.commit()
        flash(f"Роль пользователя {user.username} изменена.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/toggle", methods=["POST"])
@login_required
@admin_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    flash("Статус учётной записи изменён.", "success")
    return redirect(url_for("admin.users"))


#  Справочники  #
@admin_bp.route("/dictionaries", methods=["GET", "POST"])
@login_required
@admin_required
def dictionaries():
    if request.method == "POST":
        kind = request.form.get("kind")
        name = request.form.get("name", "").strip()
        if name:
            if kind == "category":
                db.session.add(Category(name=name))
            elif kind == "priority":
                level = int(request.form.get("level") or 0)
                db.session.add(Priority(name=name, level=level))
            elif kind == "status":
                is_closed = bool(request.form.get("is_closed"))
                db.session.add(Status(name=name, is_closed=is_closed))
            db.session.commit()
            flash("Запись добавлена.", "success")
        return redirect(url_for("admin.dictionaries"))

    return render_template("admin/dictionaries.html",
                           categories=Category.query.all(),
                           priorities=Priority.query.order_by(Priority.level).all(),
                           statuses=Status.query.all())


#  Оборудование  #
@admin_bp.route("/equipment", methods=["GET", "POST"])
@login_required
@admin_required
def equipment():
    if request.method == "POST":
        inv = request.form.get("inventory_number", "").strip()
        name = request.form.get("name", "").strip()
        etype = request.form.get("type", "").strip()
        dep_id = request.form.get("department_id") or None
        if inv and name:
            if Equipment.query.filter_by(inventory_number=inv).first():
                flash("Оборудование с таким инвентарным номером уже есть.", "error")
            else:
                db.session.add(Equipment(
                    inventory_number=inv, name=name, type=etype,
                    department_id=int(dep_id) if dep_id else None,
                ))
                db.session.commit()
                flash("Оборудование добавлено.", "success")
        return redirect(url_for("admin.equipment"))

    return render_template("admin/equipment.html",
                           equipment=Equipment.query.all(),
                           departments=Department.query.all())


#  Заявки  #
@admin_bp.route("/tickets")
@login_required
@admin_required
def tickets():
    page = request.args.get("page", 1, type=int)
    pagination = (
        Ticket.query.order_by(Ticket.created_at.desc())
        .paginate(page=page, per_page=15, error_out=False)
    )
    return render_template("admin/tickets.html", pagination=pagination)


#  База знаний  #
@admin_bp.route("/knowledge")
@login_required
@admin_required
def knowledge():
    articles = KnowledgeArticle.query.order_by(KnowledgeArticle.updated_at.desc()).all()
    return render_template("admin/knowledge.html", articles=articles)


@admin_bp.route("/knowledge/<int:article_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_article(article_id):
    article = KnowledgeArticle.query.get_or_404(article_id)
    db.session.delete(article)
    db.session.commit()
    flash("Статья удалена.", "success")
    return redirect(url_for("admin.knowledge"))


#  Отчеты #
@admin_bp.route("/reports")
@login_required
@admin_required
def reports():
    return render_template("admin/reports.html",
                           total=Ticket.query.count())


@admin_bp.route("/reports/xlsx")
@login_required
@admin_required
def report_xlsx():
    tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()
    buffer = generate_report_xlsx(tickets)
    filename = f"otchet_zayavki_{datetime.utcnow().strftime('%Y%m%d')}.xlsx"
    return send_file(buffer, as_attachment=True, download_name=filename,
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@admin_bp.route("/tickets/<int:ticket_id>/act")
@login_required
@admin_required
def ticket_act(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    buffer = generate_act_docx(ticket)
    filename = f"akt_{ticket.number}.docx"
    return send_file(buffer, as_attachment=True, download_name=filename,
                     mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
