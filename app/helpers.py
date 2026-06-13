"""Funcoes compartilhadas entre os blueprints (acesso a dados e formatacao)."""
import hashlib
from datetime import date

from flask import g


def hash_token(token: str) -> str:
    """SHA-256 hex de um token de API. So o hash e guardado no banco."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def uid():
    """ID do usuario logado (garantido pelo guard require_login)."""
    return g.user["id"]


def get_main_goal(db, user_id):
    """Meta principal = goal com priority=1 (mais alta). Pode nao existir."""
    return db.execute(
        "SELECT * FROM goals WHERE user_id = ? AND priority = 1 ORDER BY id LIMIT 1",
        (user_id,),
    ).fetchone()


def get_categories(db, type_=None):
    """Lista categorias, opcionalmente filtradas por tipo (income/expense)."""
    if type_ in ("income", "expense"):
        return db.execute(
            "SELECT * FROM categories WHERE type = ? ORDER BY name", (type_,)
        ).fetchall()
    return db.execute("SELECT * FROM categories ORDER BY type, name").fetchall()


def brl(value):
    """Formata numero como moeda brasileira: 1234.5 -> 'R$ 1.234,50'."""
    try:
        s = f"{float(value):,.2f}"
    except (TypeError, ValueError):
        return "R$ 0,00"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def date_br(value):
    """date/str ISO -> 'dd/mm/aaaa'."""
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            value = date.fromisoformat(value)
        except ValueError:
            return value
    return value.strftime("%d/%m/%Y")
