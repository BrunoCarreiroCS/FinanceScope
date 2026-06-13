"""FinanceScope - aplicacao Flask (application factory).

Autenticacao por sessao: cada usuario ve e edita apenas os proprios dados.
As rotas ficam organizadas em blueprints (blueprints/).
"""
import os
import secrets
from datetime import datetime

from flask import Flask, abort, g, redirect, request, session, url_for

import database
import seeds
from blueprints.api import bp as api_bp
from blueprints.auth import bp as auth_bp
from blueprints.goals import bp as goals_bp
from blueprints.main import bp as main_bp
from blueprints.simulator import bp as simulator_bp
from blueprints.transactions import bp as transactions_bp
from helpers import brl, date_br
from utils import finance

# Endpoints acessiveis sem login (o resto e protegido por padrao).
PUBLIC_ENDPOINTS = {"main.home", "auth.login", "auth.registro", "static"}


def create_app(test_config=None):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get(
        "SECRET_KEY", "dev-financescope-troque-em-producao"
    )
    app.config["DATABASE"] = os.path.join(app.instance_path, database.DB_FILENAME)
    # Endurecimento da sessao. SECURE so liga em producao (HTTPS) via env,
    # para nao quebrar o login em http://localhost no desenvolvimento.
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = bool(os.environ.get("SESSION_COOKIE_SECURE"))
    app.config["CSRF_ENABLED"] = True
    if test_config:
        app.config.update(test_config)

    database.init_app(app)
    seeds.register(app)

    app.jinja_env.filters["brl"] = brl
    app.jinja_env.filters["date_br"] = date_br

    def csrf_token():
        if "_csrf" not in session:
            session["_csrf"] = secrets.token_hex(16)
        return session["_csrf"]

    @app.context_processor
    def inject_globals():
        hourly = None
        user_name = None
        if getattr(g, "user", None):
            hourly = finance.hourly_value(
                g.user["monthly_income"], g.user["monthly_hours"]
            )
            user_name = (g.user["name"] or "").split(" ")[0] if g.user["name"] else None

        hour = datetime.now().hour
        if hour < 12:
            greeting = "Bom dia"
        elif hour < 18:
            greeting = "Boa tarde"
        else:
            greeting = "Boa noite"

        return {
            "app_name": "FinanceScope",
            "current_hourly": hourly,
            "user_name": user_name,
            "greeting": greeting,
            "csrf_token": csrf_token,
        }

    @app.before_request
    def load_user():
        g.user = None
        user_id = session.get("user_id")
        if user_id is not None:
            try:
                db = database.get_db()
                g.user = db.execute(
                    "SELECT * FROM users WHERE id = ?", (user_id,)
                ).fetchone()
            except Exception:
                g.user = None

    @app.before_request
    def csrf_protect():
        if not app.config.get("CSRF_ENABLED", True):
            return
        # A API usa Bearer token e precisa ficar stateless, inclusive em futuros POSTs.
        if request.path.startswith("/api/"):
            return
        if request.method == "POST":
            sent = request.form.get("csrf_token")
            real = session.get("_csrf")
            if not real or not sent or not secrets.compare_digest(sent, real):
                abort(400)

    @app.before_request
    def require_login():
        # A API (/api/*) se autentica por token, fora do fluxo de sessao.
        if request.path.startswith("/api/"):
            return
        # Tudo e protegido por padrao; paginas publicas em PUBLIC_ENDPOINTS.
        if request.endpoint in PUBLIC_ENDPOINTS or request.endpoint is None:
            return
        if g.user is None:
            return redirect(url_for("auth.login", next=request.path))

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(goals_bp)
    app.register_blueprint(simulator_bp)
    app.register_blueprint(api_bp)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
