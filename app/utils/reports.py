"""
Agregacoes do dashboard.

Junta os dados crus do SQLite e devolve numeros prontos para a tela.
Mantem o app.py enxuto e deixa a logica de montagem em um lugar so.
"""
from __future__ import annotations

import calendar
from datetime import date
from typing import Optional

from utils import finance

# Meses curtos em pt-br para os rotulos dos graficos.
MESES_CURTOS = ["jan", "fev", "mar", "abr", "mai", "jun",
                "jul", "ago", "set", "out", "nov", "dez"]


def _month_key(d: date) -> str:
    return d.strftime("%Y-%m")


def _shift_month(year: int, month: int, delta: int) -> tuple[int, int]:
    """Soma 'delta' meses a (ano, mes), tratando a virada de ano."""
    index = (year * 12 + (month - 1)) + delta
    return index // 12, index % 12 + 1


def month_totals(db, user_id: int, month_str: str) -> dict:
    """Soma receitas e despesas de um mes (YYYY-MM)."""
    rows = db.execute(
        """SELECT type, COALESCE(SUM(amount), 0) AS total
           FROM transactions
           WHERE user_id = ? AND strftime('%Y-%m', date) = ?
           GROUP BY type""",
        (user_id, month_str),
    ).fetchall()
    totals = {"income": 0.0, "expense": 0.0}
    for r in rows:
        totals[r["type"]] = r["total"]
    return totals


def expense_to_date(db, user_id: int, today: date) -> float:
    """
    Soma das despesas do mes ate hoje (inclusive).
    Base correta para a previsao de fechamento: lancamentos com data futura
    no mes nao devem inflar a media diaria.
    """
    row = db.execute(
        """SELECT COALESCE(SUM(amount), 0) AS total
           FROM transactions
           WHERE user_id = ? AND type = 'expense'
                 AND strftime('%Y-%m', date) = ?
                 AND date <= ?""",
        (user_id, today.strftime("%Y-%m"), today.isoformat()),
    ).fetchone()
    return row["total"]


def expenses_by_category(db, user_id: int, month_str: str) -> list[dict]:
    """Despesas agrupadas por categoria, da maior para a menor."""
    rows = db.execute(
        """SELECT COALESCE(c.name, 'Sem categoria') AS name,
                  COALESCE(c.color, '#7e8a99')      AS color,
                  SUM(t.amount)                     AS total
           FROM transactions t
           LEFT JOIN categories c ON c.id = t.category_id
           WHERE t.user_id = ? AND t.type = 'expense'
                 AND strftime('%Y-%m', t.date) = ?
           GROUP BY t.category_id
           ORDER BY total DESC""",
        (user_id, month_str),
    ).fetchall()
    return [dict(r) for r in rows]


def top_expenses(db, user_id: int, month_str: str, limit: int = 5) -> list[dict]:
    """Ranking das maiores despesas individuais do mes."""
    rows = db.execute(
        """SELECT t.description, t.amount, t.date,
                  COALESCE(c.name, 'Sem categoria') AS category_name,
                  COALESCE(c.color, '#7e8a99')      AS category_color
           FROM transactions t
           LEFT JOIN categories c ON c.id = t.category_id
           WHERE t.user_id = ? AND t.type = 'expense'
                 AND strftime('%Y-%m', t.date) = ?
           ORDER BY t.amount DESC
           LIMIT ?""",
        (user_id, month_str, limit),
    ).fetchall()
    return [dict(r) for r in rows]


def monthly_evolution(db, user_id: int, today: date, months: int = 6) -> dict:
    """Receitas x despesas dos ultimos N meses, em ordem cronologica."""
    start_y, start_m = _shift_month(today.year, today.month, -(months - 1))
    start_str = f"{start_y:04d}-{start_m:02d}"

    rows = db.execute(
        """SELECT strftime('%Y-%m', date) AS ym, type, SUM(amount) AS total
           FROM transactions
           WHERE user_id = ? AND strftime('%Y-%m', date) >= ?
           GROUP BY ym, type""",
        (user_id, start_str),
    ).fetchall()

    bucket = {}  # {'YYYY-MM': {'income': x, 'expense': y}}
    for r in rows:
        bucket.setdefault(r["ym"], {"income": 0.0, "expense": 0.0})
        bucket[r["ym"]][r["type"]] = r["total"]

    labels, income_series, expense_series = [], [], []
    for i in range(months):
        y, m = _shift_month(start_y, start_m, i)
        key = f"{y:04d}-{m:02d}"
        labels.append(MESES_CURTOS[m - 1])
        data = bucket.get(key, {})
        income_series.append(round(data.get("income", 0.0), 2))
        expense_series.append(round(data.get("expense", 0.0), 2))

    return {"labels": labels, "income": income_series, "expense": expense_series}


def build_alerts(user, totals: dict, forecast: float, balance: float) -> list[dict]:
    """
    Gera alertas didaticos (nao proibitivos) com base nos dados do mes.
    Cada alerta: {level: baixo|medio|alto, title, text}.
    """
    alerts = []
    income = user["monthly_income"] if user else 0
    hours = user["monthly_hours"] if user else 0
    limit = user["monthly_limit"] if user else 0

    if not income or not hours:
        alerts.append({
            "level": "medio",
            "title": "Complete seu perfil",
            "text": "Informe renda e horas mensais para liberar o custo em "
                    "horas e o impacto na renda.",
        })

    if limit and forecast > limit:
        excedente = forecast - limit
        alerts.append({
            "level": "alto",
            "title": "Previsão acima do limite",
            "text": f"No ritmo atual, o mês pode fechar cerca de "
                    f"R$ {excedente:,.2f} acima do seu limite planejado."
                    .replace(",", "X").replace(".", ",").replace("X", "."),
        })

    if balance < 0:
        alerts.append({
            "level": "alto",
            "title": "Saldo negativo",
            "text": "As despesas já superam as receitas neste mês.",
        })

    if not alerts:
        alerts.append({
            "level": "baixo",
            "title": "Tudo sob controle",
            "text": "Nenhum sinal de risco com base nos seus dados até aqui.",
        })
    return alerts


# --------------------------------------------------------------------------
# Relatorios por periodo (intervalo de datas arbitrario)
# --------------------------------------------------------------------------

def period_totals(db, user_id: int, start: str, end: str) -> dict:
    rows = db.execute(
        """SELECT type, COALESCE(SUM(amount), 0) AS total
           FROM transactions
           WHERE user_id = ? AND date BETWEEN ? AND ?
           GROUP BY type""",
        (user_id, start, end),
    ).fetchall()
    totals = {"income": 0.0, "expense": 0.0}
    for r in rows:
        totals[r["type"]] = r["total"]
    return totals


def expenses_by_category_period(db, user_id: int, start: str, end: str) -> list[dict]:
    rows = db.execute(
        """SELECT COALESCE(c.name, 'Sem categoria') AS name,
                  COALESCE(c.color, '#7e8a99')      AS color,
                  SUM(t.amount)                     AS total
           FROM transactions t
           LEFT JOIN categories c ON c.id = t.category_id
           WHERE t.user_id = ? AND t.type = 'expense'
                 AND t.date BETWEEN ? AND ?
           GROUP BY t.category_id
           ORDER BY total DESC""",
        (user_id, start, end),
    ).fetchall()
    return [dict(r) for r in rows]


def top_expenses_period(db, user_id: int, start: str, end: str, limit: int = 10) -> list[dict]:
    rows = db.execute(
        """SELECT t.description, t.amount, t.date,
                  COALESCE(c.name, 'Sem categoria') AS category_name,
                  COALESCE(c.color, '#7e8a99')      AS category_color
           FROM transactions t
           LEFT JOIN categories c ON c.id = t.category_id
           WHERE t.user_id = ? AND t.type = 'expense'
                 AND t.date BETWEEN ? AND ?
           ORDER BY t.amount DESC
           LIMIT ?""",
        (user_id, start, end, limit),
    ).fetchall()
    return [dict(r) for r in rows]


def evolution_range(db, user_id: int, start: str, end: str) -> dict:
    """Receitas x despesas por mes dentro do intervalo [start, end]."""
    rows = db.execute(
        """SELECT strftime('%Y-%m', date) AS ym, type, SUM(amount) AS total
           FROM transactions
           WHERE user_id = ? AND date BETWEEN ? AND ?
           GROUP BY ym, type""",
        (user_id, start, end),
    ).fetchall()
    bucket = {}
    for r in rows:
        bucket.setdefault(r["ym"], {"income": 0.0, "expense": 0.0})
        bucket[r["ym"]][r["type"]] = r["total"]

    sy, sm = int(start[:4]), int(start[5:7])
    ey, em = int(end[:4]), int(end[5:7])
    n = (ey * 12 + em) - (sy * 12 + sm) + 1
    n = max(1, min(n, 24))  # evita listas gigantes

    labels, income_series, expense_series = [], [], []
    for i in range(n):
        y, m = _shift_month(sy, sm, i)
        key = f"{y:04d}-{m:02d}"
        labels.append(f"{MESES_CURTOS[m - 1]}/{str(y)[2:]}")
        data = bucket.get(key, {})
        income_series.append(round(data.get("income", 0.0), 2))
        expense_series.append(round(data.get("expense", 0.0), 2))
    return {"labels": labels, "income": income_series, "expense": expense_series}


def build_report(db, user, start: str, end: str) -> dict:
    """Pacote completo do relatorio para um intervalo de datas."""
    user_id = user["id"] if user else 0
    totals = period_totals(db, user_id, start, end)
    income, expense = totals["income"], totals["expense"]

    monthly_income = user["monthly_income"] if user else 0
    monthly_hours = user["monthly_hours"] if user else 0
    expense_hours = finance.cost_in_hours(expense, monthly_income, monthly_hours)

    count = db.execute(
        """SELECT COUNT(*) AS n FROM transactions
           WHERE user_id = ? AND date BETWEEN ? AND ?""",
        (user_id, start, end),
    ).fetchone()["n"]

    evolution = evolution_range(db, user_id, start, end)
    n_months = max(1, len(evolution["labels"]))

    return {
        "start": start,
        "end": end,
        "income": income,
        "expense": expense,
        "balance": finance.month_balance(income, expense),
        "expense_hours": expense_hours,
        "expense_hours_label": finance.hours_to_hm(expense_hours),
        "categories": expenses_by_category_period(db, user_id, start, end),
        "top_expenses": top_expenses_period(db, user_id, start, end),
        "evolution": evolution,
        "count": count,
        "avg_monthly_expense": expense / n_months,
        "n_months": n_months,
    }


def build_dashboard(db, user, today: Optional[date] = None) -> dict:
    """Monta o pacote completo de dados do dashboard."""
    if today is None:
        today = date.today()
    user_id = user["id"] if user else 1
    month_str = _month_key(today)

    totals = month_totals(db, user_id, month_str)
    income, expense = totals["income"], totals["expense"]
    balance = finance.month_balance(income, expense)
    # Previsao usa apenas as despesas ate hoje (media diaria realista).
    forecast = finance.projected_closing(expense_to_date(db, user_id, today), today)

    monthly_income = user["monthly_income"] if user else 0
    monthly_hours = user["monthly_hours"] if user else 0
    expense_hours = finance.cost_in_hours(expense, monthly_income, monthly_hours)

    categories = expenses_by_category(db, user_id, month_str)
    biggest = categories[0] if categories else None

    return {
        "income": income,
        "expense": expense,
        "balance": balance,
        "forecast": forecast,
        "expense_hours": expense_hours,
        "expense_hours_label": finance.hours_to_hm(expense_hours),
        "categories": categories,
        "top_expenses": top_expenses(db, user_id, month_str),
        "biggest_category": biggest,
        "evolution": monthly_evolution(db, user_id, today),
        "alerts": build_alerts(user, totals, forecast, balance),
        "days_in_month": calendar.monthrange(today.year, today.month)[1],
    }
