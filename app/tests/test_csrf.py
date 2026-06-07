"""Testa a proteção CSRF (com o guard habilitado)."""
import os
import tempfile

import app as app_module
import database


def _app_with_csrf():
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    application = app_module.create_app(
        {"TESTING": True, "DATABASE": path, "CSRF_ENABLED": True}
    )
    with application.app_context():
        database.init_db()
    return application, path


def test_post_sem_csrf_token_e_bloqueado():
    application, path = _app_with_csrf()
    try:
        client = application.test_client()
        r = client.post("/registro", data={
            "name": "A", "email": "a@a.com",
            "password": "segredo123", "confirm": "segredo123",
        })
        assert r.status_code == 400
    finally:
        os.unlink(path)
