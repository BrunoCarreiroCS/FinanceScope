"""Testes do RealCost Engine."""
from datetime import date
import pytest

from utils import finance as f


# --- valor da hora ---------------------------------------------------------

def test_hourly_value_basico():
    assert f.hourly_value(3000, 160) == pytest.approx(18.75)


def test_hourly_value_horas_zero_retorna_none():
    assert f.hourly_value(3000, 0) is None


def test_hourly_value_horas_negativas_retorna_none():
    assert f.hourly_value(3000, -10) is None


# --- custo em horas --------------------------------------------------------

def test_cost_in_hours():
    # R$ 187,50 com hora a R$ 18,75 = 10 horas
    assert f.cost_in_hours(187.5, 3000, 160) == pytest.approx(10.0)


def test_cost_in_hours_sem_perfil_retorna_none():
    assert f.cost_in_hours(100, 0, 0) is None


# --- impacto na renda ------------------------------------------------------

def test_income_impact_pct():
    assert f.income_impact_pct(300, 3000) == pytest.approx(10.0)


def test_income_impact_renda_zero_retorna_none():
    assert f.income_impact_pct(300, 0) is None


# --- saldo do mes ----------------------------------------------------------

def test_month_balance():
    assert f.month_balance(5000, 3200) == 1800


def test_month_balance_negativo():
    assert f.month_balance(2000, 3000) == -1000


# --- previsao de fechamento -----------------------------------------------

def test_projected_closing_meio_do_mes():
    # 10 dias gastos R$ 1000 em junho (30 dias) -> 100/dia * 30 = 3000
    today = date(2026, 6, 10)
    assert f.projected_closing(1000, today=today) == pytest.approx(3000.0)


def test_projected_closing_inicio_do_mes_sem_quebrar():
    today = date(2026, 6, 1)
    # 1 dia, R$ 50 -> 50 * 30 = 1500
    assert f.projected_closing(50, today=today) == pytest.approx(1500.0)


# --- metas -----------------------------------------------------------------

def test_goal_months_remaining():
    # faltam 2000, aporte 500 -> 4 meses
    assert f.goal_months_remaining(3000, 1000, 500) == pytest.approx(4.0)


def test_goal_already_reached():
    assert f.goal_months_remaining(1000, 1500, 200) == 0


def test_goal_sem_aporte_retorna_none():
    assert f.goal_months_remaining(1000, 0, 0) is None


def test_goal_delay_months():
    # compra de 1500 com aporte 500 -> 3 meses de atraso
    assert f.goal_delay_months(1500, 500) == pytest.approx(3.0)


# --- recorrente ------------------------------------------------------------

def test_annual_recurring_cost():
    assert f.annual_recurring_cost(39.90) == pytest.approx(478.80)


# --- formatacao ------------------------------------------------------------

def test_hours_to_hm():
    assert f.hours_to_hm(3.5) == "3h30"
    assert f.hours_to_hm(0.25) == "0h15"
    assert f.hours_to_hm(None) is None


# --- classificacao de risco -----------------------------------------------

def test_classify_risk_baixo():
    assert f.classify_risk(2.0) == f.RISK_LOW


def test_classify_risk_medio():
    assert f.classify_risk(10.0) == f.RISK_MEDIUM


def test_classify_risk_alto():
    assert f.classify_risk(30.0) == f.RISK_HIGH


def test_classify_risk_sem_dados_assume_medio():
    assert f.classify_risk(None) == f.RISK_MEDIUM


# --- analise consolidada de compra ----------------------------------------

def test_analyze_purchase_completa():
    r = f.analyze_purchase(
        amount=1500,
        installments=3,
        monthly_income=3000,
        monthly_hours=160,
        monthly_contribution=500,
    )
    assert r.installment_value == pytest.approx(500.0)
    assert r.hours_cost == pytest.approx(80.0)
    assert r.hours_label == "80h00"
    assert r.income_impact_pct == pytest.approx(50.0)
    assert r.monthly_impact_pct == pytest.approx(16.666, rel=1e-2)
    assert r.risk == f.RISK_HIGH
    assert r.goal_delay_months == pytest.approx(3.0)
    assert "atrasar sua meta" in r.message


def test_analyze_purchase_sem_perfil_nao_quebra():
    r = f.analyze_purchase(amount=200, installments=1,
                           monthly_income=0, monthly_hours=0,
                           monthly_contribution=0)
    assert r.hours_cost is None
    assert r.income_impact_pct is None
    assert r.goal_delay_months is None
    assert "complete seu perfil" in r.message


# --- veredito do simulador ------------------------------------------------

def test_verdict_vale_a_pena():
    # R$ 100 em 3000 de renda = 3,3% mensal, sem atraso relevante.
    r = f.analyze_purchase(100, 1, 3000, 160, 500)
    v = f.purchase_verdict(r)
    assert v["level"] == f.RISK_LOW
    assert v["label"] == "Vale a pena"


def test_verdict_melhor_esperar():
    # R$ 300 em 3000 = 10% mensal -> faixa moderada.
    r = f.analyze_purchase(300, 1, 3000, 160, 500)
    v = f.purchase_verdict(r)
    assert v["level"] == f.RISK_MEDIUM
    assert v["label"] == "Melhor esperar"


def test_verdict_nao_compre_agora():
    # R$ 6000 em 12x = 500/mes = 16,7% mensal -> alto.
    r = f.analyze_purchase(6000, 12, 3000, 160, 500)
    v = f.purchase_verdict(r)
    assert v["level"] == f.RISK_HIGH
    assert v["label"] == "Não compre agora"


def test_verdict_sem_perfil():
    r = f.analyze_purchase(200, 1, 0, 0, 0)
    v = f.purchase_verdict(r)
    assert v["label"] == "Avalie com cuidado"
