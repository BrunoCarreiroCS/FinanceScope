#!/usr/bin/env python3
"""
financescope_consultor_mcp - consultor financeiro sobre os SEUS dados reais.

Ao contrario do server.py (stateless, calculo puro), este servidor consulta a
API read-only do FinanceScope com um token pessoal, respondendo sobre as
financas reais do dono do token.

Config por variaveis de ambiente:
  FINANCESCOPE_API_URL    base da API (padrao: http://127.0.0.1:5000)
  FINANCESCOPE_API_TOKEN  token gerado na pagina de Perfil do app

Todas as ferramentas sao somente-leitura.
"""
import json
import os
from typing import Annotated, Optional

import httpx
from pydantic import Field

from mcp.server.fastmcp import FastMCP

API_URL = os.environ.get("FINANCESCOPE_API_URL", "http://127.0.0.1:5000").rstrip("/")
API_TOKEN = os.environ.get("FINANCESCOPE_API_TOKEN", "")

mcp = FastMCP("financescope_consultor_mcp")


async def _get(path: str, params: Optional[dict] = None) -> str:
    """GET autenticado na API; devolve JSON (str) ou um erro acionavel."""
    if not API_TOKEN:
        return json.dumps({
            "error": "sem_token",
            "message": "Defina FINANCESCOPE_API_TOKEN (gere um token na pagina de Perfil "
                       "do FinanceScope).",
        }, ensure_ascii=False)
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(f"{API_URL}{path}", params=params, headers=headers)
        if r.status_code == 401:
            return json.dumps({
                "error": "unauthorized",
                "message": "Token invalido ou revogado. Gere um novo na pagina de Perfil.",
            }, ensure_ascii=False)
        r.raise_for_status()
        return json.dumps(r.json(), ensure_ascii=False, indent=2)
    except httpx.ConnectError:
        return json.dumps({
            "error": "offline",
            "message": f"Nao consegui conectar em {API_URL}. O FinanceScope esta no ar?",
        }, ensure_ascii=False)
    except httpx.HTTPStatusError as e:
        return json.dumps({
            "error": "http_error",
            "message": f"A API respondeu {e.response.status_code}.",
        }, ensure_ascii=False)


_READONLY = {
    "readOnlyHint": True, "destructiveHint": False,
    "idempotentHint": True, "openWorldHint": True,
}


@mcp.tool(name="resumo_financeiro", annotations={"title": "Resumo do mes", **_READONLY})
async def resumo_financeiro(
    mes: Annotated[Optional[str], Field(description="Mes no formato AAAA-MM (padrao: mes atual)")] = None,
) -> str:
    """Receitas, despesas e saldo do usuario num mes, com o equivalente em horas
    de trabalho das despesas. Le os dados reais via API (token).

    Args:
        mes (str|None): mes 'AAAA-MM'. Se omitido, usa o mes atual.

    Returns:
        str: JSON {month, income, expense, balance, expense_hours_label}.
    """
    return await _get("/api/resumo", {"month": mes} if mes else None)


@mcp.tool(name="gastos_por_categoria", annotations={"title": "Gastos por categoria", **_READONLY})
async def gastos_por_categoria(
    mes: Annotated[Optional[str], Field(description="Mes no formato AAAA-MM (padrao: mes atual)")] = None,
) -> str:
    """Despesas do usuario agrupadas por categoria (com % do total) num mes.

    Args:
        mes (str|None): mes 'AAAA-MM'. Se omitido, usa o mes atual.

    Returns:
        str: JSON {month, total, categorias: [{nome, total, percentual}]}.
    """
    return await _get("/api/categorias", {"month": mes} if mes else None)


@mcp.tool(name="status_meta", annotations={"title": "Status da meta", **_READONLY})
async def status_meta() -> str:
    """Progresso e prazo estimado da meta principal do usuario.

    Returns:
        str: JSON {has_goal, nome, alvo, atual, falta, aporte_mensal,
        progresso_pct, meses_restantes} ou {has_goal: false}.
    """
    return await _get("/api/meta")


@mcp.tool(name="posso_comprar", annotations={"title": "Posso comprar? (dados reais)", **_READONLY})
async def posso_comprar(
    valor: Annotated[float, Field(gt=0, description="Valor total da compra em R$")],
    parcelas: Annotated[int, Field(ge=1, le=48, description="Numero de parcelas (1 = a vista)")] = 1,
) -> str:
    """Roda o RealCost usando o PERFIL REAL do usuario (renda, horas e aporte
    da meta vem do banco — nao precisa informar). Retorna veredito de decisao.

    Args:
        valor (float): valor total da compra em R$.
        parcelas (int): numero de parcelas (1 = a vista).

    Returns:
        str: JSON com custo_em_horas, impacto, risco, atraso_meta, veredito e mensagem.
    """
    return await _get("/api/posso-comprar", {"valor": valor, "parcelas": parcelas})


if __name__ == "__main__":
    mcp.run()
