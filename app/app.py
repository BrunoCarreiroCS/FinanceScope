"""FinanceScope - aplicacao Flask (MVP).

Sem login: usamos um usuario fixo (id=1) criado pelo schema.sql.
"""
from flask import Flask, render_template, g

import database

DEFAULT_USER_ID = 1


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "dev-financescope"  # trocar em producao
    database.init_app(app)

    @app.context_processor
    def inject_globals():
        return {"app_name": "FinanceScope"}

    @app.before_request
    def load_user():
        try:
            db = database.get_db()
            g.user = db.execute(
                "SELECT * FROM users WHERE id = ?", (DEFAULT_USER_ID,)
            ).fetchone()
        except Exception:
            g.user = None

    # --- Rotas placeholder (serao implementadas nas proximas fases) ---

    @app.route("/")
    def dashboard():
        return render_template("dashboard.html", active="dashboard")

    @app.route("/perfil")
    def perfil():
        return render_template("perfil.html", active="perfil")

    @app.route("/transacoes")
    def transacoes():
        return render_template("transacoes.html", active="transacoes")

    @app.route("/metas")
    def metas():
        return render_template("metas.html", active="metas")

    @app.route("/simulador")
    def simulador():
        return render_template("simulador.html", active="simulador")

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
