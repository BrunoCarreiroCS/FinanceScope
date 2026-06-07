"""Testes das agregacoes do dashboard (utils/reports.py)."""
import os
import sqlite3
from datetime import date

import pytest

from utils import reports


SCHEMA = os.path.join(os.path.dirname(__file__), "..", "schema.sql")


@pytest.fixture
def db():
    """Banco em memoria com o schema real e algumas transacoes de junho/2026."""
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    with open(SCHEMA, "r", encoding="utf-8") as f:
        con.executescript(f.read())

    con.execute("UPDATE users SET monthly_income=3000, monthly_hours=160, monthly_limit=2500 WHERE id=1")
    linhas = [
        ("income",  "Salário",   1, 3000, "2026-06-05"),
        ("expense", "Aluguel",   5, 1200, "2026-06-06"),
        ("expense", "Mercado",   4,  500, "2026-06-08"),
        ("expense", "Uber",      6,  100, "2026-05-20"),  # mes anterior
    ]
    for tipo, desc, cat, valor, dia in linhas:
        con.execute(
            """INSERT INTO transactions (user_id, type, description, category_id, amount, date)
               VALUES (1, ?, ?, ?, ?, ?)""",
            (tipo, desc, cat, valor, dia),
        )
    con.commit()
    yield con
    con.close()


def test_month_totals_soma_apenas_o_mes(db):
    totais = reports.month_totals(db, 1, "2026-06")
    assert totais["income"] == pytest.approx(3000)
    assert totais["expense"] == pytest.approx(1700)  # 1200 + 500 (Uber e de maio)


def test_expenses_by_category_ordena_desc(db):
    cats = reports.expenses_by_category(db, 1, "2026-06")
    assert cats[0]["name"] == "Moradia"      # 1200
    assert cats[0]["total"] == pytest.approx(1200)
    assert cats[1]["name"] == "Alimentação"  # 500


def test_top_expenses_respeita_limite(db):
    top = reports.top_expenses(db, 1, "2026-06", limit=1)
    assert len(top) == 1
    assert top[0]["description"] == "Aluguel"


def test_expense_to_date_ignora_lancamentos_futuros(db):
    # Em 07/06: so o Aluguel (06/06) entra; Mercado (08/06) fica de fora.
    total = reports.expense_to_date(db, 1, date(2026, 6, 7))
    assert total == pytest.approx(1200)


def test_monthly_evolution_tem_6_meses(db):
    evo = reports.monthly_evolution(db, 1, date(2026, 6, 7))
    assert len(evo["labels"]) == 6
    assert evo["labels"][-1] == "jun"
    assert evo["expense"][-1] == pytest.approx(1700)
    assert evo["expense"][-2] == pytest.approx(100)  # maio


def test_shift_month_vira_o_ano():
    assert reports._shift_month(2026, 1, -1) == (2025, 12)
    assert reports._shift_month(2026, 12, 1) == (2027, 1)


def test_build_alerts_previsao_acima_do_limite():
    user = {"monthly_income": 3000, "monthly_hours": 160, "monthly_limit": 2000}
    alerts = reports.build_alerts(user, {"income": 3000, "expense": 1700}, forecast=2500, balance=1300)
    niveis = [a["level"] for a in alerts]
    assert "alto" in niveis


def test_build_alerts_perfil_incompleto():
    user = {"monthly_income": 0, "monthly_hours": 0, "monthly_limit": 0}
    alerts = reports.build_alerts(user, {"income": 0, "expense": 0}, forecast=0, balance=0)
    assert any("perfil" in a["title"].lower() for a in alerts)


def test_build_dashboard_pacote_completo(db):
    user = db.execute("SELECT * FROM users WHERE id=1").fetchone()
    data = reports.build_dashboard(db, user, today=date(2026, 6, 7))
    assert data["income"] == pytest.approx(3000)
    assert data["expense"] == pytest.approx(1700)
    assert data["balance"] == pytest.approx(1300)
    assert data["biggest_category"]["name"] == "Moradia"
    assert data["expense_hours_label"] is not None  # perfil completo
