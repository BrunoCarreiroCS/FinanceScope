"""Testes da API read-only autenticada por token (blueprints/api.py)."""
import re
from datetime import date


def _gen_token(client) -> str:
    """Gera um token para o usuario logado e extrai o texto puro da pagina."""
    r = client.post("/perfil/token", data={}, follow_redirects=True)
    m = re.search(r'token-box">([^<]+)<', r.get_data(as_text=True))
    assert m, "token nao apareceu na pagina de perfil"
    return m.group(1)


def _add_expense(client, amount, desc="Teste"):
    client.post("/transacoes/nova", data={
        "type": "expense", "description": desc,
        "amount": str(amount), "date": date.today().isoformat(),
    })


def test_api_sem_token_retorna_401(client):
    r = client.get("/api/resumo")
    assert r.status_code == 401
    assert r.get_json()["error"] == "unauthorized"


def test_api_token_invalido_retorna_401(client):
    r = client.get("/api/resumo", headers={"Authorization": "Bearer naoexiste"})
    assert r.status_code == 401


def test_api_resumo_com_token_valido(client, auth_user):
    _add_expense(client, 100)
    token = _gen_token(client)
    r = client.get("/api/resumo", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.get_json()
    assert data["expense"] == 100
    assert data["month"] == date.today().strftime("%Y-%m")


def test_api_gerar_token_invalida_o_anterior(client, auth_user):
    t1 = _gen_token(client)
    t2 = _gen_token(client)
    assert t1 != t2
    # O antigo deixa de funcionar.
    assert client.get("/api/resumo", headers={"Authorization": f"Bearer {t1}"}).status_code == 401
    assert client.get("/api/resumo", headers={"Authorization": f"Bearer {t2}"}).status_code == 200


def test_api_revogar_token(client, auth_user):
    token = _gen_token(client)
    client.post("/perfil/token", data={"action": "revogar"})
    assert client.get("/api/resumo", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_api_isola_dados_por_usuario(client, auth_user):
    # Ana (auth_user) tem uma despesa de 100 e um token.
    _add_expense(client, 100, "Ana expense")
    token_ana = _gen_token(client)
    # Troca para o Bob, com despesa diferente.
    client.post("/sair")
    client.post("/registro", data={
        "name": "Bob", "email": "bob@teste.com",
        "password": "segredo123", "confirm": "segredo123",
    })
    _add_expense(client, 999, "Bob expense")
    # O token da Ana so enxerga os dados da Ana.
    r = client.get("/api/resumo", headers={"Authorization": f"Bearer {token_ana}"})
    assert r.get_json()["expense"] == 100


def test_api_posso_comprar_usa_perfil(client, auth_user):
    # Define renda/horas no perfil.
    client.post("/perfil", data={
        "name": "Ana", "monthly_income": "4000", "monthly_hours": "160",
        "monthly_limit": "0",
    })
    token = _gen_token(client)
    r = client.get(
        "/api/posso-comprar?valor=350&parcelas=1",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    data = r.get_json()
    assert data["custo_em_horas"] == "14h00"   # 350 / (4000/160) = 14h
    assert "veredito" in data and "rotulo" in data["veredito"]
