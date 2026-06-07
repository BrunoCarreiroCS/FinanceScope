"""FinanceScope - aplicacao Flask (MVP).

Sem login: usamos um usuario fixo (id=1) criado pelo schema.sql.
"""
from flask import Flask, render_template, redirect, url_for, request, flash, g

import database
from utils import finance
from utils.forms import parse_decimal

DEFAULT_USER_ID = 1


def get_main_goal(db, user_id):
    """Meta principal = goal com priority=1 (mais alta). Pode nao existir."""
    return db.execute(
        "SELECT * FROM goals WHERE user_id = ? AND priority = 1 ORDER BY id LIMIT 1",
        (user_id,),
    ).fetchone()


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "dev-financescope"  # trocar em producao
    database.init_app(app)

    @app.context_processor
    def inject_globals():
        hourly = None
        if getattr(g, "user", None):
            hourly = finance.hourly_value(
                g.user["monthly_income"], g.user["monthly_hours"]
            )
        return {"app_name": "FinanceScope", "current_hourly": hourly}

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

    @app.route("/perfil", methods=["GET", "POST"])
    def perfil():
        db = database.get_db()
        main_goal = get_main_goal(db, DEFAULT_USER_ID)

        if request.method == "POST":
            errors = {}
            form = {
                "name": (request.form.get("name") or "").strip(),
                "monthly_income": request.form.get("monthly_income", ""),
                "monthly_hours": request.form.get("monthly_hours", ""),
                "monthly_limit": request.form.get("monthly_limit", ""),
                "goal_name": (request.form.get("goal_name") or "").strip(),
                "goal_target": request.form.get("goal_target", ""),
                "goal_contribution": request.form.get("goal_contribution", ""),
            }

            if not form["name"]:
                errors["name"] = "Informe um nome."

            income, e = parse_decimal(form["monthly_income"])
            if e:
                errors["monthly_income"] = e
            hours, e = parse_decimal(form["monthly_hours"])
            if e:
                errors["monthly_hours"] = e
            limit, e = parse_decimal(form["monthly_limit"])
            if e:
                errors["monthly_limit"] = e

            # Meta principal e opcional; se qualquer campo for preenchido, validamos o conjunto.
            goal_filled = any([form["goal_name"], form["goal_target"], form["goal_contribution"]])
            target = contribution = None
            if goal_filled:
                if not form["goal_name"]:
                    errors["goal_name"] = "Informe o nome da meta."
                target, e = parse_decimal(form["goal_target"])
                if e:
                    errors["goal_target"] = e
                elif not target or target <= 0:
                    errors["goal_target"] = "O valor alvo deve ser maior que zero."
                contribution, e = parse_decimal(form["goal_contribution"])
                if e:
                    errors["goal_contribution"] = e

            if errors:
                flash("Verifique os campos destacados.", "error")
                return render_template(
                    "perfil.html", active="perfil",
                    form=form, errors=errors, main_goal=main_goal,
                ), 400

            db.execute(
                """UPDATE users
                   SET name = ?, monthly_income = ?, monthly_hours = ?,
                       monthly_limit = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (form["name"], income, hours, limit, DEFAULT_USER_ID),
            )

            if goal_filled:
                if main_goal:
                    db.execute(
                        """UPDATE goals
                           SET name = ?, target_amount = ?, monthly_contribution = ?,
                               updated_at = CURRENT_TIMESTAMP
                           WHERE id = ?""",
                        (form["goal_name"], target, contribution or 0, main_goal["id"]),
                    )
                else:
                    db.execute(
                        """INSERT INTO goals
                           (user_id, name, target_amount, current_amount,
                            monthly_contribution, priority)
                           VALUES (?, ?, ?, 0, ?, 1)""",
                        (DEFAULT_USER_ID, form["goal_name"], target, contribution or 0),
                    )

            db.commit()
            flash("Perfil salvo com sucesso.", "success")
            return redirect(url_for("perfil"))

        # GET: pre-preenche com dados do banco.
        user = g.user
        form = {
            "name": user["name"] if user else "",
            "monthly_income": user["monthly_income"] if user else 0,
            "monthly_hours": user["monthly_hours"] if user else 0,
            "monthly_limit": user["monthly_limit"] if user else 0,
            "goal_name": main_goal["name"] if main_goal else "",
            "goal_target": main_goal["target_amount"] if main_goal else "",
            "goal_contribution": main_goal["monthly_contribution"] if main_goal else "",
        }
        return render_template(
            "perfil.html", active="perfil", form=form, errors={}, main_goal=main_goal,
        )

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
