"""Paginas principais: landing, dashboard, relatorios e perfil."""
from datetime import date

from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)

import database
from helpers import get_main_goal, uid
from utils import reports
from utils.forms import parse_date, parse_decimal

bp = Blueprint("main", __name__)


@bp.route("/")
def home():
    return render_template("home.html")


@bp.route("/app")
def dashboard():
    db = database.get_db()
    data = reports.build_dashboard(db, g.user)
    return render_template("dashboard.html", active="dashboard", d=data)


@bp.route("/relatorios")
def relatorios():
    db = database.get_db()
    today = date.today()
    # Periodo padrao: do 1o dia de 2 meses atras ate hoje (~3 meses).
    y, m = today.year, today.month - 2
    while m < 1:
        m += 12
        y -= 1
    default_start = date(y, m, 1).isoformat()

    start = request.args.get("start") or default_start
    end = request.args.get("end") or today.isoformat()
    _, e1 = parse_date(start)
    _, e2 = parse_date(end)
    if e1 or e2:
        start, end = default_start, today.isoformat()
    elif start > end:
        start, end = end, start

    # Atalhos de periodo para os chips da UI (estado refletido na URL).
    y3, m3 = today.year, today.month - 2
    while m3 < 1:
        m3 += 12
        y3 -= 1
    quick = {
        "mes": {"start": today.replace(day=1).isoformat(), "end": today.isoformat()},
        "tri": {"start": date(y3, m3, 1).isoformat(), "end": today.isoformat()},
        "ano": {"start": date(today.year, 1, 1).isoformat(), "end": today.isoformat()},
    }

    data = reports.build_report(db, g.user, start, end)
    return render_template(
        "relatorios.html", active="relatorios", d=data,
        start=start, end=end, quick=quick,
    )


@bp.route("/perfil", methods=["GET", "POST"])
def perfil():
    db = database.get_db()
    main_goal = get_main_goal(db, uid())

    if request.method == "POST":
        errors = {}
        form = {
            "name": (request.form.get("name") or "").strip(),
            "monthly_income": request.form.get("monthly_income", ""),
            "monthly_hours": request.form.get("monthly_hours", ""),
            "monthly_limit": request.form.get("monthly_limit", ""),
            "goal_name": (request.form.get("goal_name") or "").strip(),
            "goal_target": request.form.get("goal_target", ""),
            "goal_contribution": request.form.get("goal_contribution", ""),
        }

        if not form["name"]:
            errors["name"] = "Informe um nome."

        income, e = parse_decimal(form["monthly_income"])
        if e:
            errors["monthly_income"] = e
        hours, e = parse_decimal(form["monthly_hours"])
        if e:
            errors["monthly_hours"] = e
        limit, e = parse_decimal(form["monthly_limit"])
        if e:
            errors["monthly_limit"] = e

        # Meta principal e opcional; se qualquer campo for preenchido, validamos o conjunto.
        goal_filled = any([form["goal_name"], form["goal_target"], form["goal_contribution"]])
        target = contribution = None
        if goal_filled:
            if not form["goal_name"]:
                errors["goal_name"] = "Informe o nome da meta."
            target, e = parse_decimal(form["goal_target"])
            if e:
                errors["goal_target"] = e
            elif not target or target <= 0:
                errors["goal_target"] = "O valor alvo deve ser maior que zero."
            contribution, e = parse_decimal(form["goal_contribution"])
            if e:
                errors["goal_contribution"] = e

        if errors:
            flash("Verifique os campos destacados.", "error")
            return render_template(
                "perfil.html", active="perfil",
                form=form, errors=errors, main_goal=main_goal,
            ), 400

        db.execute(
            """UPDATE users
               SET name = ?, monthly_income = ?, monthly_hours = ?,
                   monthly_limit = ?, updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (form["name"], income, hours, limit, uid()),
        )

        if goal_filled:
            if main_goal:
                db.execute(
                    """UPDATE goals
                       SET name = ?, target_amount = ?, monthly_contribution = ?,
                           updated_at = CURRENT_TIMESTAMP
                       WHERE id = ?""",
                    (form["goal_name"], target, contribution or 0, main_goal["id"]),
                )
            else:
                db.execute(
                    """INSERT INTO goals
                       (user_id, name, target_amount, current_amount,
                        monthly_contribution, priority)
                       VALUES (?, ?, ?, 0, ?, 1)""",
                    (uid(), form["goal_name"], target, contribution or 0),
                )

        db.commit()
        flash("Perfil salvo com sucesso.", "success")
        return redirect(url_for("main.perfil"))

    # GET: pre-preenche com dados do banco.
    user = g.user
    form = {
        "name": user["name"] if user else "",
        "monthly_income": user["monthly_income"] if user else 0,
        "monthly_hours": user["monthly_hours"] if user else 0,
        "monthly_limit": user["monthly_limit"] if user else 0,
        "goal_name": main_goal["name"] if main_goal else "",
        "goal_target": main_goal["target_amount"] if main_goal else "",
        "goal_contribution": main_goal["monthly_contribution"] if main_goal else "",
    }
    return render_template(
        "perfil.html", active="perfil", form=form, errors={}, main_goal=main_goal,
    )
