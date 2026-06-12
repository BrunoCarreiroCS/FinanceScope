#!/usr/bin/env python3
"""
financescope_mcp - servidor MCP do RealCost Engine.

Expoe o motor de calculo do FinanceScope (app/utils/finance.py) como
ferramentas que um cliente MCP (ex.: Claude Desktop) pode chamar. E
*stateless*: nao acessa banco nem dados de usuario - quem fornece os
numeros (renda, horas, aporte) e a propria conversa.

Reusa a logica ja coberta pelos testes em app/tests/test_finance.py.
"""
import json
import os
import sys
from typing import Annotated, Optional

from pydantic import Field

from mcp.server.fastmcp import FastMCP

# Torna o RealCost Engine importavel sem duplicar logica.
# finance.py e puro (so usa a stdlib), entao basta colocar app/ no path.
_APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app"))
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)

from utils import finance  # noqa: E402  (precisa do sys.path acima)

mcp = FastMCP("financescope_mcp")


def _round(value: Optional[float], digits: int = 2) -> Optional[float]:
    """Arredonda mantendo None (perfil incompleto) intacto."""
    return round(value, digits) if value is not None else None


@mcp.tool(
    name="analisar_compra",
    annotations={
        "title": "Analisar compra (RealCost)",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
def analisar_compra(
    valor: Annotated[float, Field(gt=0, description="Valor total da compra em R$ (ex.: 3000)")],
    renda_mensal: Annotated[float, Field(ge=0, description="Renda mensal liquida em R$ (ex.: 4000)")],
    horas_mensais: Annotated[float, Field(ge=0, description="Horas trabalhadas no mes (ex.: 160)")],
    parcelas: Annotated[int, Field(ge=1, le=48, description="Numero de parcelas (1 = a vista)")] = 1,
    aporte_meta: Annotated[float, Field(ge=0, description="Quanto a pessoa guarda por mes na meta principal (R$); 0 se nao houver meta")] = 0,
) -> str:
    """Analisa o custo real de uma compra: tempo de trabalho, impacto na renda,
    atraso na meta e um veredito de decisao ("Vale a pena" / "Melhor esperar" /
    "Nao compre agora").

    Use quando a pessoa pergunta se vale a pena comprar algo e informa (ou voce
    consegue inferir) renda, horas mensais e quanto guarda por mes. Calculo puro,
    nao acessa dados de ninguem.

    Args:
        valor (float): valor total da compra em R$.
        renda_mensal (float): renda mensal liquida em R$.
        horas_mensais (float): horas trabalhadas no mes.
        parcelas (int): numero de parcelas (1 = a vista). Padrao 1.
        aporte_meta (float): quanto guarda por mes na meta (0 se nao houver). Padrao 0.

    Returns:
        str: JSON com o schema:
        {
          "valor": float,
          "parcelas": int,
          "valor_parcela": float,
          "custo_em_horas": str|null,            # ex.: "120h00"
          "custo_em_horas_decimal": float|null,
          "impacto_na_renda_pct": float|null,    # % do valor total sobre a renda
          "impacto_mensal_pct": float|null,      # % da parcela sobre a renda
          "risco": str,                          # "baixo" | "medio" | "alto"
          "atraso_meta": str|null,               # ex.: "6 meses" / "sem impacto"
          "veredito": {"nivel": str, "rotulo": str, "motivo": str},
          "mensagem": str                        # frase humanizada pronta
        }
        Campos null indicam perfil incompleto (renda/horas ausentes).
    """
    a = finance.analyze_purchase(
        amount=valor,
        installments=parcelas,
        monthly_income=renda_mensal,
        monthly_hours=horas_mensais,
        monthly_contribution=aporte_meta,
    )
    verdict = finance.purchase_verdict(a)
    result = {
        "valor": valor,
        "parcelas": a.installments,
        "valor_parcela": _round(a.installment_value),
        "custo_em_horas": a.hours_label,
        "custo_em_horas_decimal": _round(a.hours_cost),
        "impacto_na_renda_pct": _round(a.income_impact_pct, 1),
        "impacto_mensal_pct": _round(a.monthly_impact_pct, 1),
        "risco": a.risk,
        "atraso_meta": a.goal_delay_label,
        "veredito": {
            "nivel": verdict["level"],
            "rotulo": verdict["label"],
            "motivo": verdict["reason"],
        },
        "mensagem": a.message,
    }
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool(
    name="custo_em_horas",
    annotations={
        "title": "Custo em horas de trabalho",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
def custo_em_horas(
    valor: Annotated[float, Field(gt=0, description="Valor da compra em R$ (ex.: 350)")],
    renda_mensal: Annotated[float, Field(ge=0, description="Renda mensal liquida em R$ (ex.: 4000)")],
    horas_mensais: Annotated[float, Field(ge=0, description="Horas trabalhadas no mes (ex.: 160)")],
) -> str:
    """Converte um valor em horas de trabalho: valor / (renda_mensal / horas_mensais).

    Use para a pergunta direta "quantas horas de trabalho isso custa?" sem
    precisar do veredito completo. Calculo puro.

    Args:
        valor (float): valor da compra em R$.
        renda_mensal (float): renda mensal liquida em R$.
        horas_mensais (float): horas trabalhadas no mes.

    Returns:
        str: JSON com o schema:
        {
          "valor": float,
          "custo_em_horas": str|null,            # ex.: "18h40"
          "custo_em_horas_decimal": float|null,
          "valor_da_hora": float|null,           # renda / horas
          "observacao": str
        }
    """
    horas = finance.cost_in_hours(valor, renda_mensal, horas_mensais)
    hv = finance.hourly_value(renda_mensal, horas_mensais)
    if horas is None:
        result = {
            "valor": valor,
            "custo_em_horas": None,
            "custo_em_horas_decimal": None,
            "valor_da_hora": None,
            "observacao": "Informe renda mensal e horas mensais (maiores que zero) "
                          "para calcular o custo em horas.",
        }
    else:
        result = {
            "valor": valor,
            "custo_em_horas": finance.hours_to_hm(horas),
            "custo_em_horas_decimal": _round(horas),
            "valor_da_hora": _round(hv),
            "observacao": "Custo em tempo de trabalho com base na renda e horas informadas.",
        }
    return json.dumps(result, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    mcp.run()
