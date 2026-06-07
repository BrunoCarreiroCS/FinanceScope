"""
RealCost Engine - formulas centrais do FinanceScope.

Todas as funcoes sao puras e sem efeitos colaterais. Sempre que um divisor
puder ser zero, retornamos None em vez de levantar excecao - a camada de
apresentacao decide como pedir ao usuario para completar o perfil financeiro.

Referencia: PDF "Plano de Desenvolvimento" secao 5 (Regras de calculo).
"""
from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date
from typing import Optional

# --- Calculos base ---------------------------------------------------------

def hourly_value(monthly_income: float, monthly_hours: float) -> Optional[float]:
    """valor_da_hora = renda_mensal / horas_mensais"""
    if not monthly_hours or monthly_hours <= 0:
        return None
    return monthly_income / monthly_hours


def cost_in_hours(amount: float, monthly_income: float, monthly_hours: float) -> Optional[float]:
    """custo_em_horas = valor / valor_da_hora"""
    hv = hourly_value(monthly_income, monthly_hours)
    if hv is None or hv <= 0:
        return None
    return amount / hv


def income_impact_pct(amount: float, monthly_income: float) -> Optional[float]:
    """impacto_na_renda = (valor / renda_mensal) * 100"""
    if not monthly_income or monthly_income <= 0:
        return None
    return (amount / monthly_income) * 100.0


def month_balance(total_income: float, total_expenses: float) -> float:
    """saldo_do_mes = total_receitas - total_despesas"""
    return total_income - total_expenses


def projected_closing(total_expenses_so_far: float, today: Optional[date] = None) -> float:
    """previsao_fechamento = media_diaria_despesas * dias_do_mes"""
    if today is None:
        today = date.today()
    days_passed = today.day
    if days_passed <= 0:
        return 0.0
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    daily_avg = total_expenses_so_far / days_passed
    return daily_avg * days_in_month


def goal_months_remaining(target: float, current: float, monthly_contribution: float) -> Optional[float]:
    """tempo_da_meta = (valor_alvo - valor_atual) / aporte_mensal"""
    if not monthly_contribution or monthly_contribution <= 0:
        return None
    remaining = max(target - current, 0)
    return remaining / monthly_contribution


def goal_delay_months(purchase_amount: float, monthly_contribution: float) -> Optional[float]:
    """atraso_da_meta = valor_compra / aporte_mensal"""
    if not monthly_contribution or monthly_contribution <= 0:
        return None
    return purchase_amount / monthly_contribution


def annual_recurring_cost(monthly_amount: float) -> float:
    """custo_anual_recorrente = valor_mensal * 12"""
    return monthly_amount * 12


# --- Helpers de apresentacao ----------------------------------------------

def hours_to_hm(hours: Optional[float]) -> Optional[str]:
    """3.5 -> '3h30'. Usado no simulador e detalhes de despesa."""
    if hours is None:
        return None
    total_minutes = int(round(hours * 60))
    h, m = divmod(total_minutes, 60)
    return f"{h}h{m:02d}"


# --- Classificacao de risco ------------------------------------------------

RISK_LOW = "baixo"
RISK_MEDIUM = "medio"
RISK_HIGH = "alto"


def classify_risk(impact_pct: Optional[float]) -> str:
    """
    Classifica o risco de uma compra/despesa pelo impacto na renda mensal.
    Faixas conservadoras; podem ser calibradas conforme feedback.
      < 5%   -> baixo
      5-15%  -> medio
      > 15%  -> alto
    Sem dados de renda -> 'medio' (nao bloqueia, mas avisa).
    """
    if impact_pct is None:
        return RISK_MEDIUM
    if impact_pct < 5:
        return RISK_LOW
    if impact_pct <= 15:
        return RISK_MEDIUM
    return RISK_HIGH


# --- Resultado consolidado do simulador "Posso Comprar?" ------------------

@dataclass
class PurchaseAnalysis:
    amount: float
    installments: int
    installment_value: float
    hours_cost: Optional[float]
    hours_label: Optional[str]
    income_impact_pct: Optional[float]
    monthly_impact_pct: Optional[float]
    risk: str
    goal_delay_months: Optional[float]
    message: str


def purchase_verdict(analysis: "PurchaseAnalysis") -> dict:
    """
    Sugestao de decisao para o simulador "Posso Comprar?".

    Nao e uma ordem: traduz o impacto em uma recomendacao explicavel, no
    espirito do produto (ajudar a decidir, nao mandar). Usa o impacto MENSAL
    (por parcela) como driver principal - assim parcelar muda o veredito - e
    considera tambem o atraso na meta.

    Retorna {level, label, reason}, onde level reaproveita as cores de risco
    (baixo=verde, medio=amarelo, alto=vermelho).
    """
    impact = analysis.monthly_impact_pct
    delay = analysis.goal_delay_months or 0

    if impact is None:
        return {
            "level": RISK_MEDIUM,
            "label": "Avalie com cuidado",
            "reason": "Complete seu perfil (renda e horas) para uma recomendação "
                      "mais precisa.",
        }

    if impact < 5 and delay <= 1:
        return {
            "level": RISK_LOW,
            "label": "Vale a pena",
            "reason": "O impacto mensal é baixo e cabe no seu orçamento, com base "
                      "nos seus dados.",
        }

    if impact <= 15:
        return {
            "level": RISK_MEDIUM,
            "label": "Melhor esperar",
            "reason": "O impacto é moderado. Pode valer a pena juntar um pouco "
                      "antes ou rever o parcelamento.",
        }

    return {
        "level": RISK_HIGH,
        "label": "Não compre agora",
        "reason": "O impacto mensal é alto e, no ritmo atual, pode comprometer "
                  "seu orçamento e atrasar suas metas.",
    }


def analyze_purchase(
    amount: float,
    installments: int,
    monthly_income: float,
    monthly_hours: float,
    monthly_contribution: float = 0,
) -> PurchaseAnalysis:
    """Calcula o impacto completo de uma compra simulada."""
    installments = max(int(installments or 1), 1)
    installment_value = amount / installments

    hours = cost_in_hours(amount, monthly_income, monthly_hours)
    impact = income_impact_pct(amount, monthly_income)
    monthly_impact = income_impact_pct(installment_value, monthly_income)
    risk = classify_risk(impact)
    delay = goal_delay_months(amount, monthly_contribution)

    parts = []
    if hours is not None:
        parts.append(f"equivale a {hours_to_hm(hours)} de trabalho")
    if impact is not None:
        parts.append(f"representa {impact:.1f}% da sua renda mensal")
    if delay is not None and delay > 0:
        parts.append(f"pode atrasar sua meta em {delay:.1f} meses")
    body = "; ".join(parts) if parts else "complete seu perfil financeiro para uma analise completa"
    message = f"Esta compra {body}, considerando os dados informados no perfil."

    return PurchaseAnalysis(
        amount=amount,
        installments=installments,
        installment_value=installment_value,
        hours_cost=hours,
        hours_label=hours_to_hm(hours),
        income_impact_pct=impact,
        monthly_impact_pct=monthly_impact,
        risk=risk,
        goal_delay_months=delay,
        message=message,
    )
