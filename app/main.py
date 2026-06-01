"""Публичная часть сайта и общий вход в личный кабинет"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.extensions import db
from app.models import (
    Ticket, Category, Status, Priority, KnowledgeArticle, Feedback,
)

main_bp = Blueprint("main", __name__)

#  Публичные страницы
@main_bp.route("/")
def index():
    articles = KnowledgeArticle.query.filter_by(is_published=True).limit(3).all()
    return render_template("public/index.html", articles=articles)


@main_bp.route("/about")
def about():
    return render_template("public/about.html")


@main_bp.route("/how-to")
def how_to():
    return render_template("public/how_to.html")


@main_bp.route("/services")
def services():
    categories = Category.query.all()
    return render_template("public/services.html", categories=categories)


@main_bp.route("/sla")
def sla():
    return render_template("public/sla.html")


@main_bp.route("/faq")
def faq():
    return render_template("public/faq.html")


@main_bp.route("/knowledge")
def knowledge():
    q = request.args.get("q", "").strip()
    query = KnowledgeArticle.query.filter_by(is_published=True)
    if q:
        query = query.filter(KnowledgeArticle.title.contains(q))
    articles = query.all()
    return render_template("public/knowledge.html", articles=articles, q=q)


@main_bp.route("/knowledge/<int:article_id>")
def knowledge_article(article_id):
    article = KnowledgeArticle.query.get_or_404(article_id)
    return render_template("public/knowledge_article.html", article=article)


@main_bp.route("/news")
def news():
    return render_template("public/news.html")


@main_bp.route("/contacts")
def contacts():
    return render_template("public/contacts.html")


@main_bp.route("/feedback", methods=["GET", "POST"])
def feedback():
    if request.method == "POST":
        user_name = request.form.get("user_name", "").strip()
        email = request.form.get("email", "").strip()
        message = request.form.get("message", "").strip()
        rating = request.form.get("rating") or None

        if not user_name or not message:
            flash("Пожалуйста, укажите имя и текст сообщения.", "error")
        elif email and "@" not in email:
            flash("Указан некорректный адрес электронной почты.", "error")
        else:
            fb = Feedback(user_name=user_name, email=email, message=message,
                          rating=int(rating) if rating else None)
            db.session.add(fb)
            db.session.commit()
            flash("Спасибо! Ваше сообщение отправлено.", "success")
            return redirect(url_for("main.feedback"))

    return render_template("public/feedback.html")


@main_bp.route("/track", methods=["GET", "POST"])
def track():
    ticket = None
    searched = False
    if request.method == "POST":
        number = request.form.get("number", "").strip()
        searched = True
        ticket = Ticket.query.filter_by(number=number).first()
        if ticket is None:
            flash("Заявка с указанным номером не найдена.", "error")
    return render_template("public/track.html", ticket=ticket, searched=searched)

#  Маршрутизация в личный кабинет по роли
@main_bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for("admin.dashboard"))
    if current_user.is_specialist:
        return redirect(url_for("specialist.queue"))
    return redirect(url_for("tickets.my_tickets"))
