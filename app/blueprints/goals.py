"""Metas financeiras: CRUD com progresso e prazo estimado."""
from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

import database
from helpers import uid
from utils import finance
from utils.forms import parse_decimal

bp = Blueprint("goals", __name__)


def _goal_view(row):
    """Enriquece uma meta com progresso (%) e meses estimados."""
    target = row["target_amount"] or 0
    current = row["current_amount"] or 0
    contribution = row["monthly_contribution"] or 0
    progress = min((current / target * 100) if target > 0 else 0, 100)
    months = finance.goal_months_remaining(target, current, contribution)
    return {
        "id": row["id"],
        "name": row["name"],
        "target_amount": target,
        "current_amount": current,
        "monthly_contribution": contribution,
        "priority": row["priority"],
        "progress": progress,
        "remaining": max(target - current, 0),
        "months": months,
        "done": current >= target,
    }


def _validate_goal(form):
    """Valida o form de meta. Retorna (dados, errors)."""
    errors, data = {}, {}
    data["name"] = (form.get("name") or "").strip()
    if not data["name"]:
        errors["name"] = "Informe o nome da meta."

    target, e = parse_decimal(form.get("target_amount"))
    if e:
        errors["target_amount"] = e
    elif not target or target <= 0:
        errors["target_amount"] = "O valor alvo deve ser maior que zero."
    data["target_amount"] = target

    current, e = parse_decimal(form.get("current_amount"))
    if e:
        errors["current_amount"] = e
    data["current_amount"] = current or 0

    contribution, e = parse_decimal(form.get("monthly_contribution"))
    if e:
        errors["monthly_contribution"] = e
    data["monthly_contribution"] = contribution or 0

    try:
        data["priority"] = int(form.get("priority") or 2)
    except ValueError:
        data["priority"] = 2
    return data, errors


@bp.route("/metas")
def metas():
    db = database.get_db()
    rows = db.execute(
        "SELECT * FROM goals WHERE user_id = ? ORDER BY priority, id",
        (uid(),),
    ).fetchall()
    goals = [_goal_view(r) for r in rows]
    return render_template("metas.html", active="metas", goals=goals)


@bp.route("/metas/nova", methods=["GET", "POST"])
def meta_nova():
    db = database.get_db()
    if request.method == "POST":
        data, errors = _validate_goal(request.form)
        if errors:
            flash("Verifique os campos destacados.", "error")
            return render_template(
                "meta_form.html", active="metas",
                form=request.form, errors=errors, mode="nova",
            ), 400
        db.execute(
            """INSERT INTO goals
               (user_id, name, target_amount, current_amount,
                monthly_contribution, priority)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (uid(), data["name"], data["target_amount"],
             data["current_amount"], data["monthly_contribution"], data["priority"]),
        )
        db.commit()
        flash("Meta criada.", "success")
        return redirect(url_for("goals.metas"))

    form = {"priority": 2, "current_amount": 0}
    return render_template(
        "meta_form.html", active="metas", form=form, errors={}, mode="nova",
    )


@bp.route("/metas/<int:goal_id>/editar", methods=["GET", "POST"])
def meta_editar(goal_id):
    db = database.get_db()
    goal = db.execute(
        "SELECT * FROM goals WHERE id = ? AND user_id = ?",
        (goal_id, uid()),
    ).fetchone()
    if goal is None:
        flash("Meta não encontrada.", "error")
        return redirect(url_for("goals.metas"))

    if request.method == "POST":
        data, errors = _validate_goal(request.form)
        if errors:
            flash("Verifique os campos destacados.", "error")
            return render_template(
                "meta_form.html", active="metas",
                form=request.form, errors=errors, mode="editar", goal_id=goal_id,
            ), 400
        db.execute(
            """UPDATE goals
               SET name = ?, target_amount = ?, current_amount = ?,
                   monthly_contribution = ?, priority = ?, updated_at = CURRENT_TIMESTAMP
               WHERE id = ? AND user_id = ?""",
            (data["name"], data["target_amount"], data["current_amount"],
             data["monthly_contribution"], data["priority"], goal_id, uid()),
        )
        db.commit()
        flash("Meta atualizada.", "success")
        return redirect(url_for("goals.metas"))

    return render_template(
        "meta_form.html", active="metas", form=goal, errors={},
        mode="editar", goal_id=goal_id,
    )


@bp.route("/metas/<int:goal_id>/excluir", methods=["POST"])
def meta_excluir(goal_id):
    db = database.get_db()
    db.execute(
        "DELETE FROM goals WHERE id = ? AND user_id = ?",
        (goal_id, uid()),
    )
    db.commit()
    flash("Meta excluída.", "success")
    return redirect(url_for("goals.metas"))
