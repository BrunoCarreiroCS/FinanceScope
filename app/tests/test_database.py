"""Testes das migracoes leves de database.py."""
import sqlite3

import database


def test_ensure_schema_cria_indice_do_token():
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.execute(
        """CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        )"""
    )

    database._ensure_schema(con)

    cols = {row["name"] for row in con.execute("PRAGMA table_info(users)").fetchall()}
    indexes = {
        row["name"]
        for row in con.execute("PRAGMA index_list(users)").fetchall()
    }
    assert "api_token_hash" in cols
    assert "idx_users_api_token_hash" in indexes
