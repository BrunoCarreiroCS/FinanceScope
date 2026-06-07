"""Helpers de parsing e validacao de formularios."""
from __future__ import annotations

from datetime import datetime
from typing import Optional, Tuple


def parse_decimal(raw: Optional[str]) -> Tuple[Optional[float], Optional[str]]:
    """
    Converte string em float aceitando virgula ou ponto.
    Retorna (valor, erro). String vazia/None -> (0.0, None).
    """
    if raw is None:
        return 0.0, None
    s = raw.strip().replace(".", "").replace(",", ".") if _looks_br(raw) else raw.strip()
    if s == "":
        return 0.0, None
    try:
        value = float(s)
    except ValueError:
        return None, "Informe um número válido."
    if value < 0:
        return None, "O valor não pode ser negativo."
    return value, None


def parse_date(raw: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """Valida data no formato YYYY-MM-DD (input HTML). Retorna (iso_str, erro)."""
    if not raw or not raw.strip():
        return None, "Informe a data."
    try:
        datetime.strptime(raw.strip(), "%Y-%m-%d")
    except ValueError:
        return None, "Data inválida."
    return raw.strip(), None


def _looks_br(raw: str) -> bool:
    """Heuristica simples: '1.234,56' (BR) vs '1234.56'. Detecta virgula decimal."""
    return "," in raw


def parse_int(raw: Optional[str], default: int = 0) -> Tuple[Optional[int], Optional[str]]:
    if raw is None or raw.strip() == "":
        return default, None
    try:
        value = int(float(raw.strip().replace(",", ".")))
    except ValueError:
        return None, "Informe um número inteiro válido."
    if value < 0:
        return None, "O valor não pode ser negativo."
    return value, None
