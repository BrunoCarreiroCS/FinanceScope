"""API REST read-only, autenticada por token (consumida pelo MCP consultor).

Stateless: nao usa sessao nem CSRF. Cada requisicao manda o token no header
'Authorization: Bearer <token>'. So leitura — nenhuma rota muta dados.
"""
from datetime import date
from functools import wraps

from flask import Blueprint, g, jsonify, request

import database
from helpers import get_main_goal, hash_token
from utils import finance, reports

bp = Blueprint("api", __name__, url_prefix="/api")


def _user_from_token():
    """Retorna o usuario dono do Bearer token, ou None."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth[7:].strip()
    if not token:
        return None
    db = database.get_db()
    return db.execute(
        "SELECT * FROM users WHERE api_token_hash = ?", (hash_token(token),)
    ).fetchone()


def require_token(fn):
    """Garante token valido; injeta o usuario em g.api_user."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = _user_from_token()
        if user is None:
            return jsonify({
                "error": "unauthorized",
                "message": "Token ausente ou invalido. Envie 'Authorization: Bearer <token>'. "
                           "Gere um token na pagina de Perfil.",
            }), 401
        g.api_user = user
        return fn(*args, **kwargs)
    return wrapper


def _current_month():
    return date.today().strftime("%Y-%m")


@bp.get("/resumo")
@require_token
def resumo():
    """Receitas, despesas e saldo de um mes (?month=YYYY-MM; padrao: mes atual)."""
    db = database.get_db()
    user = g.api_user
    month = request.args.get("month") or _current_month()
    totals = reports.month_totals(db, user["id"], month)
    income, expense = totals["income"], totals["expense"]
    expense_hours = finance.cost_in_hours(
        expense, user["monthly_income"], user["monthly_hours"]
    )
    return jsonify({
        "month": month,
        "income": round(income, 2),
        "expense": round(expense, 2),
        "balance": round(finance.month_balance(income, expense), 2),
        "expense_hours_label": finance.hours_to_hm(expense_hours),
    })


@bp.get("/categorias")
@require_token
def categorias():
    """Despesas por categoria de um mes (?month=YYYY-MM), maior para menor."""
    db = database.get_db()
    month = request.args.get("month") or _current_month()
    cats = reports.expenses_by_category(db, g.api_user["id"], month)
    total = sum(c["total"] for c in cats) or 0
    return jsonify({
        "month": month,
        "total": round(total, 2),
        "categorias": [
            {
                "nome": c["name"],
                "total": round(c["total"], 2),
                "percentual": round(c["total"] / total * 100, 1) if total else 0,
            }
            for c in cats
        ],
    })


@bp.get("/meta")
@require_token
def meta():
    """Status da meta principal: progresso e prazo estimado."""
    db = database.get_db()
    goal = get_main_goal(db, g.api_user["id"])
    if goal is None:
        return jsonify({"has_goal": False, "message": "Nenhuma meta principal definida."})
    target = goal["target_amount"] or 0
    current = goal["current_amount"] or 0
    contribution = goal["monthly_contribution"] or 0
    months = finance.goal_months_remaining(target, current, contribution)
    return jsonify({
        "has_goal": True,
        "nome": goal["name"],
        "alvo": round(target, 2),
        "atual": round(current, 2),
        "falta": round(max(target - current, 0), 2),
        "aporte_mensal": round(contribution, 2),
        "progresso_pct": round(min(current / target * 100, 100), 1) if target else 0,
        "meses_restantes": round(months, 1) if months is not None else None,
    })


@bp.get("/posso-comprar")
@require_token
def posso_comprar():
    """Roda o RealCost com o perfil do usuario (?valor=&parcelas=)."""
    user = g.api_user
    try:
        valor = float(request.args.get("valor", ""))
    except (TypeError, ValueError):
        return jsonify({"error": "bad_request", "message": "Informe 'valor' numerico (R$)."}), 400
    if valor <= 0:
        return jsonify({"error": "bad_request", "message": "'valor' deve ser maior que zero."}), 400
    try:
        parcelas = max(int(request.args.get("parcelas", 1)), 1)
    except (TypeError, ValueError):
        parcelas = 1

    db = database.get_db()
    goal = get_main_goal(db, user["id"])
    contribution = goal["monthly_contribution"] if goal else 0
    a = finance.analyze_purchase(
        amount=valor, installments=parcelas,
        monthly_income=user["monthly_income"], monthly_hours=user["monthly_hours"],
        monthly_contribution=contribution,
    )
    verdict = finance.purchase_verdict(a)
    return jsonify({
        "valor": valor,
        "parcelas": a.installments,
        "custo_em_horas": a.hours_label,
        "impacto_na_renda_pct": round(a.income_impact_pct, 1) if a.income_impact_pct is not None else None,
        "impacto_mensal_pct": round(a.monthly_impact_pct, 1) if a.monthly_impact_pct is not None else None,
        "risco": a.risk,
        "atraso_meta": a.goal_delay_label,
        "veredito": {"nivel": verdict["level"], "rotulo": verdict["label"], "motivo": verdict["reason"]},
        "mensagem": a.message,
    })
