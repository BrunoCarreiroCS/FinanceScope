"""Testa o parser flexivel de CSV de extratos."""
from utils.csv_import import parse_amount, parse_csv, parse_date


def test_parse_amount_aceita_formatos_comuns():
    assert parse_amount("1.234,56") == 1234.56
    assert parse_amount("1234.56") == 1234.56
    assert parse_amount("R$ -50,00") == -50.0
    assert parse_amount("(50,00)") == -50.0
    assert parse_amount("") is None


def test_parse_date_aceita_iso_e_br():
    assert parse_date("2026-06-05") == "2026-06-05"
    assert parse_date("05/06/2026") == "2026-06-05"
    assert parse_date("nao-e-data") is None


def test_parse_csv_cabecalhos_br_e_separador_pt_virgula():
    raw = (
        "data;descricao;valor\n"
        "05/06/2026;Salario;3000,00\n"
        "06/06/2026;Aluguel;-1200,00\n"
    ).encode("utf-8")
    rows, errors = parse_csv(raw)
    assert errors == []
    assert len(rows) == 2
    assert rows[0]["type"] == "income"  and rows[0]["amount"] == 3000.0
    assert rows[1]["type"] == "expense" and rows[1]["amount"] == 1200.0


def test_parse_csv_ignora_linhas_invalidas():
    raw = (
        "Data,Descricao,Valor\n"
        "2026-06-05,Ok,100\n"
        "lixo,sem valor,abc\n"
    ).encode("utf-8")
    rows, errors = parse_csv(raw)
    assert len(rows) == 1
    assert any("Linha" in e for e in errors)


def test_parse_csv_sem_colunas_obrigatorias():
    raw = b"foo,bar\n1,2\n"
    rows, errors = parse_csv(raw)
    assert rows == [] and errors
