"""Simulador "Posso comprar?": veredito de decisao antes do gasto."""
import json
from dataclasses import asdict

from flask import Blueprint, flash, g, render_template, request

import database
from helpers import get_categories, get_main_goal, uid
from utils import finance
from utils.forms import parse_decimal

bp = Blueprint("simulator", __name__)


@bp.route("/simulador", methods=["GET", "POST"])
def simulador():
    db = database.get_db()
    categories = get_categories(db, "expense")
    result = None
    verdict = None
    form = {"installments": 1, "priority": "media"}

    if request.method == "POST":
        errors = {}
        form = {
            "item_name": (request.form.get("item_name") or "").strip(),
            "amount": request.form.get("amount", ""),
            "category_id": request.form.get("category_id") or "",
            "installments": request.form.get("installments", "1"),
            "priority": request.form.get("priority", "media"),
        }
        if not form["item_name"]:
            errors["item_name"] = "Informe o item."
        amount, e = parse_decimal(form["amount"])
        if e:
            errors["amount"] = e
        elif not amount or amount <= 0:
            errors["amount"] = "O valor deve ser maior que zero."
        try:
            installments = max(int(form["installments"]), 1)
        except (ValueError, TypeError):
            installments = 1

        if errors:
            flash("Verifique os campos destacados.", "error")
            return render_template(
                "simulador.html", active="simulador",
                categories=categories, form=form, errors=errors,
                result=None, verdict=None,
            ), 400

        main_goal = get_main_goal(db, uid())
        contribution = main_goal["monthly_contribution"] if main_goal else 0
        user = g.user
        result = finance.analyze_purchase(
            amount=amount,
            installments=installments,
            monthly_income=user["monthly_income"] if user else 0,
            monthly_hours=user["monthly_hours"] if user else 0,
            monthly_contribution=contribution,
        )
        verdict = finance.purchase_verdict(result)

        # Guarda a simulacao (alimenta historico/relatorios futuros).
        db.execute(
            """INSERT INTO purchase_simulations
               (user_id, item_name, amount, category_id, installments,
                risk_level, result_json)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (uid(), form["item_name"], amount,
             int(form["category_id"]) if form["category_id"] else None,
             installments, result.risk, json.dumps(asdict(result))),
        )
        db.commit()

    return render_template(
        "simulador.html", active="simulador",
        categories=categories, form=form, errors={}, result=result, verdict=verdict,
    )
