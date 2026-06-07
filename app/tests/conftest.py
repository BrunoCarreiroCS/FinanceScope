"""Fixtures de teste: app com banco SQLite temporario e isolado."""
import os
import sys
import tempfile

import pytest

# Garante que os modulos da app (app.py, database.py) sejam importaveis.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import app as app_module  # noqa: E402
import database  # noqa: E402


@pytest.fixture
def app():
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    application = app_module.create_app(
        {"TESTING": True, "DATABASE": path, "CSRF_ENABLED": False}
    )
    with application.app_context():
        database.init_db()
    yield application
    os.unlink(path)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_user(client):
    """Cria e loga um usuario de teste; retorna os dados usados."""
    data = {"name": "Ana", "email": "ana@teste.com",
            "password": "segredo123", "confirm": "segredo123"}
    client.post("/registro", data=data)
    return data
