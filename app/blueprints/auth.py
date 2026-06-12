"""Autenticacao: registro, login e logout."""
from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

import database

bp = Blueprint("auth", __name__)


@bp.route("/registro", methods=["GET", "POST"])
def registro():
    if g.user:
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm") or ""
        errors = {}
        if not name:
            errors["name"] = "Informe seu nome."
        if "@" not in email or "." not in email:
            errors["email"] = "Informe um e-mail válido."
        if len(password) < 6:
            errors["password"] = "A senha deve ter ao menos 6 caracteres."
        if password != confirm:
            errors["confirm"] = "As senhas não conferem."

        db = database.get_db()
        if not errors and db.execute(
            "SELECT 1 FROM users WHERE email = ?", (email,)
        ).fetchone():
            errors["email"] = "Já existe uma conta com esse e-mail."

        if errors:
            flash("Verifique os campos destacados.", "error")
            return render_template(
                "registro.html", form={"name": name, "email": email}, errors=errors
            ), 400

        cur = db.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, generate_password_hash(password)),
        )
        db.commit()
        session.clear()
        session["user_id"] = cur.lastrowid
        flash("Conta criada! Comece preenchendo seu perfil financeiro.", "success")
        return redirect(url_for("main.perfil"))
    return render_template("registro.html", form={}, errors={})


@bp.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        db = database.get_db()
        user = db.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
        if user is None or not check_password_hash(user["password_hash"], password):
            flash("E-mail ou senha incorretos.", "error")
            return render_template("login.html", form={"email": email}), 400
        session.clear()
        session["user_id"] = user["id"]
        nxt = request.args.get("next")
        return redirect(nxt if nxt and nxt.startswith("/") else url_for("main.dashboard"))
    return render_template("login.html", form={})


@bp.route("/sair", methods=["POST"])
def sair():
    session.clear()
    flash("Você saiu da sua conta.", "success")
    return redirect(url_for("main.home"))
