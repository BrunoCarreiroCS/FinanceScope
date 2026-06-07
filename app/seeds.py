"""
Dados de demonstracao do FinanceScope.

Cria (ou recria) um usuario demo com login, perfil, uma meta e algumas
transacoes do mes atual, para que o dashboard, os graficos e o ranking
aparecam preenchidos sem cadastrar tudo na mao. Util para prints e demo.

Uso: flask seed-demo
Credenciais: demo@financescope.app / demo1234
"""
from datetime import date

from werkzeug.security import generate_password_hash

import database

DEMO_EMAIL = "demo@financescope.app"
DEMO_PASSWORD = "demo1234"


def _d(day: int) -> str:
    """Data do dia 'day' no mes atual, no formato YYYY-MM-DD."""
    hoje = date.today()
    return f"{hoje.year:04d}-{hoje.month:02d}-{day:02d}"


def seed_demo(db) -> int:
    pwd = generate_password_hash(DEMO_PASSWORD)
    row = db.execute("SELECT id FROM users WHERE email = ?", (DEMO_EMAIL,)).fetchone()

    if row:
        user_id = row["id"]
        # Limpa os dados do demo, mantendo a conta.
        db.execute("DELETE FROM transactions WHERE user_id = ?", (user_id,))
        db.execute("DELETE FROM goals WHERE user_id = ?", (user_id,))
        db.execute("DELETE FROM purchase_simulations WHERE user_id = ?", (user_id,))
        db.execute(
            """UPDATE users
               SET name = ?, password_hash = ?, monthly_income = ?,
                   monthly_hours = ?, monthly_limit = ?
               WHERE id = ?""",
            ("Bruno", pwd, 3000, 160, 2500, user_id),
        )
    else:
        cur = db.execute(
            """INSERT INTO users
               (name, email, password_hash, monthly_income, monthly_hours, monthly_limit)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("Bruno", DEMO_EMAIL, pwd, 3000, 160, 2500),
        )
        user_id = cur.lastrowid

    # Meta principal (priority = 1).
    db.execute(
        """INSERT INTO goals
           (user_id, name, target_amount, current_amount, monthly_contribution, priority)
           VALUES (?, ?, ?, ?, ?, 1)""",
        (user_id, "Reserva de emergência", 10000, 2500, 500),
    )

    # Transacoes do mes (category_id segue a ordem do seed em schema.sql).
    transacoes = [
        # tipo,      descricao,      cat, valor,   dia, pagamento, recorrente
        ("income",  "Salário",         1, 3000.00, 5,  "Pix",     0),
        ("income",  "Freelance",       2,  650.00, 12, "Pix",     0),
        ("expense", "Aluguel",         5, 1200.00, 6,  "Boleto",  1),
        ("expense", "Mercado",         4,  520.90, 8,  "Cartão",  0),
        ("expense", "Uber",            6,  180.50, 9,  "Cartão",  0),
        ("expense", "Netflix",        10,   39.90, 10, "Cartão",  1),
        ("expense", "Academia",        8,   99.90, 10, "Pix",     1),
        ("expense", "Restaurante",     7,  240.00, 14, "Cartão",  0),
        ("expense", "Farmácia",        8,   87.30, 15, "Pix",     0),
    ]
    for tipo, desc, cat, valor, dia, pag, rec in transacoes:
        db.execute(
            """INSERT INTO transactions
               (user_id, type, description, category_id, amount, date, payment_method, is_recurring)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, tipo, desc, cat, valor, _d(dia), pag, rec),
        )

    db.commit()
    return user_id


def register(app):
    @app.cli.command("seed-demo")
    def seed_demo_command():
        """flask seed-demo -> cria o usuario demo com dados de exemplo."""
        seed_demo(database.get_db())
        print("Dados de demonstração inseridos.")
        print(f"Login: {DEMO_EMAIL}  |  Senha: {DEMO_PASSWORD}")
