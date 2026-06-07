"""Testes do fluxo de autenticacao (registro, login, logout, protecao)."""
import database


def test_registro_cria_conta_e_loga(client):
    r = client.post("/registro", data={
        "name": "Ana", "email": "ana@teste.com",
        "password": "segredo123", "confirm": "segredo123",
    }, follow_redirects=True)
    assert r.status_code == 200
    # Apos registrar, o usuario ja entra logado e acessa o app.
    assert client.get("/app").status_code == 200


def test_registro_senha_curta(client):
    r = client.post("/registro", data={
        "name": "Ana", "email": "ana@teste.com",
        "password": "123", "confirm": "123",
    })
    assert r.status_code == 400


def test_registro_senhas_diferentes(client):
    r = client.post("/registro", data={
        "name": "Ana", "email": "ana@teste.com",
        "password": "segredo123", "confirm": "outra123",
    })
    assert r.status_code == 400


def test_registro_email_duplicado(client, auth_user):
    client.post("/sair")
    r = client.post("/registro", data={
        "name": "Outro", "email": auth_user["email"],
        "password": "segredo123", "confirm": "segredo123",
    })
    assert r.status_code == 400


def test_senha_e_armazenada_com_hash(client, app, auth_user):
    with app.app_context():
        db = database.get_db()
        row = db.execute(
            "SELECT password_hash FROM users WHERE email = ?", (auth_user["email"],)
        ).fetchone()
    assert row is not None
    # Nunca em texto puro; deve ser um hash (scrypt/pbkdf2 do werkzeug).
    assert row["password_hash"] != auth_user["password"]
    assert ":" in row["password_hash"]


def test_login_senha_errada(client, auth_user):
    client.post("/sair")
    r = client.post("/login", data={
        "email": auth_user["email"], "password": "errada999",
    })
    assert r.status_code == 400


def test_login_correto(client, auth_user):
    client.post("/sair")
    r = client.post("/login", data={
        "email": auth_user["email"], "password": auth_user["password"],
    }, follow_redirects=True)
    assert r.status_code == 200
    assert client.get("/app").status_code == 200


def test_rota_protegida_sem_login_redireciona(client):
    r = client.get("/app")
    assert r.status_code == 302
    assert "/login" in r.headers["Location"]


def test_logout_encerra_sessao(client, auth_user):
    assert client.get("/app").status_code == 200  # logado
    client.post("/sair")
    r = client.get("/app")
    assert r.status_code == 302  # deslogado -> redireciona


def test_usuarios_nao_veem_dados_um_do_outro(client, app):
    # Usuario A cria uma transacao.
    client.post("/registro", data={"name": "A", "email": "a@t.com",
                                    "password": "segredo123", "confirm": "segredo123"})
    client.post("/transacoes/nova", data={
        "type": "expense", "description": "Segredo do A",
        "amount": "100", "date": "2026-06-01",
    })
    client.post("/sair")
    # Usuario B nao deve ver a transacao do A.
    client.post("/registro", data={"name": "B", "email": "b@t.com",
                                    "password": "segredo123", "confirm": "segredo123"})
    r = client.get("/transacoes")
    assert b"Segredo do A" not in r.data
