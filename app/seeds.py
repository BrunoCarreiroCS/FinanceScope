"""
Dados de demonstracao do FinanceScope.

Popula o banco com um perfil, uma meta e algumas transacoes do mes atual,
para que o dashboard, os graficos e o ranking apareçam preenchidos sem
precisar cadastrar tudo na mao. Util para prints e apresentacao.

Uso: flask seed-demo
"""
from datetime import date

import database


def _d(day: int) -> str:
    """Data do dia 'day' no mes atual, no formato YYYY-MM-DD."""
    hoje = date.today()
    return f"{hoje.year:04d}-{hoje.month:02d}-{day:02d}"


def seed_demo(db) -> None:
    # Limpa dados transacionais, mantendo as categorias padrao.
    db.execute("DELETE FROM transactions")
    db.execute("DELETE FROM goals")
    db.execute("DELETE FROM purchase_simulations")

    # Perfil de exemplo.
    db.execute(
        """UPDATE users
           SET name = ?, monthly_income = ?, monthly_hours = ?, monthly_limit = ?
           WHERE id = 1""",
        ("Bruno", 3000, 160, 2500),
    )

    # Meta principal (priority = 1).
    db.execute(
        """INSERT INTO goals
           (user_id, name, target_amount, current_amount, monthly_contribution, priority)
           VALUES (1, ?, ?, ?, ?, 1)""",
        ("Reserva de emergência", 10000, 2500, 500),
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
               VALUES (1, ?, ?, ?, ?, ?, ?, ?)""",
            (tipo, desc, cat, valor, _d(dia), pag, rec),
        )

    db.commit()


def register(app):
    @app.cli.command("seed-demo")
    def seed_demo_command():
        """flask seed-demo -> popula o banco com dados de exemplo."""
        seed_demo(database.get_db())
        print("Dados de demonstração inseridos.")
