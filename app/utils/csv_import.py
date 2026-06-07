"""
Importacao de extratos/faturas em CSV.

Faz um parsing tolerante: detecta o separador (',' ou ';'), reconhece as
colunas por nome de cabecalho (data, descricao, valor) e aceita datas e
valores em formatos comuns (BR e ISO). Valores negativos viram despesa;
positivos, receita.
"""
from __future__ import annotations

import csv
import io
import unicodedata
from datetime import datetime

DATE_KEYS = ["data", "date", "dia", "datalancamento", "datadolancamento"]
DESC_KEYS = ["descricao", "description", "historico", "lancamento", "memo",
             "titulo", "estabelecimento", "detalhe", "detalhes"]
AMOUNT_KEYS = ["valor", "amount", "value", "quantia", "montante"]

MAX_ROWS = 1000


def _norm(s: str) -> str:
    """minuscula, sem acento e sem espacos — para casar cabecalhos."""
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.strip().lower().replace(" ", "").replace("_", "")


def _find_col(headers_map: dict, keys: list) -> str | None:
    for k in keys:
        if k in headers_map:
            return headers_map[k]
    # match parcial (ex.: "valor (r$)")
    for norm, original in headers_map.items():
        if any(k in norm for k in keys):
            return original
    return None


def parse_date(raw: str):
    raw = (raw or "").strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%Y/%m/%d"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def parse_amount(raw: str):
    """Aceita '1.234,56', '1234.56', 'R$ -50,00', '(50,00)'. Retorna float (com sinal)."""
    s = (raw or "").strip()
    if not s:
        return None
    # Considera negativo se houver "-" em qualquer lugar, ou parenteses
    # (estilo contabil: "(50,00)" = -50,00).
    negative = "-" in s or (s.startswith("(") and s.endswith(")"))
    s = s.replace("R$", "").replace("(", "").replace(")", "").replace("+", "")
    s = s.replace(" ", "").replace("-", "")
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")      # BR: 1.234,56
    elif "," in s:
        s = s.replace(",", ".")                        # 1234,56
    try:
        value = float(s)
    except ValueError:
        return None
    return -value if negative else value


def parse_csv(raw_bytes: bytes):
    """
    Retorna (rows, errors).
    rows: lista de {date, description, amount(positivo), type}.
    """
    text = raw_bytes.decode("utf-8-sig", errors="replace")
    if not text.strip():
        return [], ["O arquivo está vazio."]

    sample = text[:4096]
    delim = ";" if sample.count(";") > sample.count(",") else ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delim)
    if not reader.fieldnames:
        return [], ["Não consegui ler o cabeçalho do arquivo."]

    headers_map = {_norm(h): h for h in reader.fieldnames if h}
    date_col = _find_col(headers_map, DATE_KEYS)
    amount_col = _find_col(headers_map, AMOUNT_KEYS)
    desc_col = _find_col(headers_map, DESC_KEYS)

    if not date_col or not amount_col:
        return [], [
            "Não encontrei as colunas necessárias. O CSV precisa ter "
            "cabeçalhos de data e valor (ex.: data, descrição, valor)."
        ]

    rows, errors = [], []
    for i, line in enumerate(reader, start=2):
        if len(rows) >= MAX_ROWS:
            errors.append(f"Importação limitada às primeiras {MAX_ROWS} linhas.")
            break
        d = parse_date(line.get(date_col, ""))
        amt = parse_amount(line.get(amount_col, ""))
        if d is None or amt is None or amt == 0:
            errors.append(f"Linha {i}: data ou valor inválido — ignorada.")
            continue
        desc = (line.get(desc_col, "") if desc_col else "").strip() or "Importado"
        rows.append({
            "date": d,
            "description": desc[:120],
            "amount": round(abs(amt), 2),
            "type": "income" if amt >= 0 else "expense",
        })
    return rows, errors
