"""Аутентификация"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from app.extensions import db
from app.models import User, Role, Department

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()

        if user is None or not user.check_password(password):
            flash("Неверное имя пользователя или пароль.", "error")
        elif not user.is_active:
            flash("Учётная запись заблокирована.", "error")
        else:
            login_user(user)
            flash(f"Добро пожаловать, {user.full_name}!", "success")
            return redirect(url_for("main.dashboard"))

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    departments = Department.query.all()

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        full_name = request.form.get("full_name", "").strip()
        password = request.form.get("password", "")
        department_id = request.form.get("department_id") or None

        errors = []
        if not username or not email or not full_name or not password:
            errors.append("Все обязательные поля должны быть заполнены.")
        if User.query.filter_by(username=username).first():
            errors.append("Пользователь с таким логином уже существует.")
        if User.query.filter_by(email=email).first():
            errors.append("Пользователь с такой почтой уже существует.")
        if len(password) < 5:
            errors.append("Пароль должен содержать не менее 5 символов.")

        if errors:
            for e in errors:
                flash(e, "error")
        else:
            role = Role.query.filter_by(name="Пользователь").first()
            user = User(username=username, email=email, full_name=full_name,
                        role=role, department_id=department_id)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash("Регистрация успешна. Теперь вы можете войти.", "success")
            return redirect(url_for("auth.login"))

    return render_template("auth/register.html", departments=departments)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Вы вышли из системы.", "success")
    return redirect(url_for("main.index"))
