"""Conexao e inicializacao do banco SQLite."""
import os
import sqlite3

from flask import current_app, g

DB_FILENAME = "financescope.sqlite"


def get_db_path():
    # Permite sobrescrever o caminho (ex.: banco temporario em testes).
    return current_app.config.get("DATABASE") or os.path.join(
        current_app.instance_path, DB_FILENAME
    )


def get_db():
    if "db" not in g:
        os.makedirs(current_app.instance_path, exist_ok=True)
        g.db = sqlite3.connect(get_db_path())
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
        _ensure_schema(g.db)
    return g.db


def _ensure_schema(db):
    """Migracao leve e idempotente: garante colunas adicionadas apos o MVP.

    Bancos antigos (criados antes do token de API) ganham a coluna sem
    precisar de ALTER manual no deploy. Custa um PRAGMA por conexao.
    """
    cols = {row["name"] for row in db.execute("PRAGMA table_info(users)").fetchall()}
    if "api_token_hash" not in cols:
        db.execute("ALTER TABLE users ADD COLUMN api_token_hash TEXT")
        db.commit()


def close_db(_=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Recria o schema. Apaga dados existentes."""
    os.makedirs(current_app.instance_path, exist_ok=True)
    db = sqlite3.connect(get_db_path())
    schema_path = os.path.join(current_app.root_path, "schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        db.executescript(f.read())
    db.commit()
    db.close()


def init_app(app):
    app.teardown_appcontext(close_db)

    @app.cli.command("init-db")
    def init_db_command():
        """flask init-db -> cria o banco do zero."""
        init_db()
        print(f"Banco criado em {os.path.join(app.instance_path, DB_FILENAME)}")
