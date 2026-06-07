"""FinanceScope - aplicacao Flask.

Autenticacao por sessao: cada usuario ve e edita apenas os proprios dados.
"""
import json
import os
import secrets
from dataclasses import asdict
from datetime import date, datetime

from flask import (Flask, render_template, redirect, url_for, request,
                   flash, session, g, abort)
from werkzeug.security import generate_password_hash, check_password_hash

import database
import seeds
from utils import finance, reports
from utils.csv_import import parse_csv
from utils.forms import parse_decimal, parse_date


def uid():
    """ID do usuario logado (garantido pelo guard require_login)."""
    return g.user["id"]


def get_main_goal(db, user_id):
    """Meta principal = goal com priority=1 (mais alta). Pode nao existir."""
    return db.execute(
        "SELECT * FROM goals WHERE user_id = ? AND priority = 1 ORDER BY id LIMIT 1",
        (user_id,),
    ).fetchone()


def get_categories(db, type_=None):
    """Lista categorias, opcionalmente filtradas por tipo (income/expense)."""
    if type_ in ("income", "expense"):
        return db.execute(
            "SELECT * FROM categories WHERE type = ? ORDER BY name", (type_,)
        ).fetchall()
    return db.execute("SELECT * FROM categories ORDER BY type, name").fetchall()


def brl(value):
    """Formata numero como moeda brasileira: 1234.5 -> 'R$ 1.234,50'."""
    try:
        s = f"{float(value):,.2f}"
    except (TypeError, ValueError):
        return "R$ 0,00"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def date_br(value):
    """date/str ISO -> 'dd/mm/aaaa'."""
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            value = date.fromisoformat(value)
        except ValueError:
            return value
    return value.strftime("%d/%m/%Y")


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

    def csrf_token():
        if "_csrf" not in session:
            session["_csrf"] = secrets.token_hex(16)
        return session["_csrf"]
    database.init_app(app)
    seeds.register(app)

    app.jinja_env.filters["brl"] = brl
    app.jinja_env.filters["date_br"] = date_br

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
        if request.method == "POST":
            sent = request.form.get("csrf_token")
            real = session.get("_csrf")
            if not real or not sent or not secrets.compare_digest(sent, real):
                abort(400)

    PUBLIC_ENDPOINTS = {"home", "login", "registro", "static"}

    @app.before_request
    def require_login():
        # Tudo e protegido por padrao; paginas publicas em PUBLIC_ENDPOINTS.
        if request.endpoint in PUBLIC_ENDPOINTS or request.endpoint is None:
            return
        if g.user is None:
            return redirect(url_for("login", next=request.path))

    # --- Autenticacao ------------------------------------------------------

    @app.route("/registro", methods=["GET", "POST"])
    def registro():
        if g.user:
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            name = (request.form.get("name") or "").strip()
            email = (request.form.get("email") or "").strip().lower()
            password = request.form.get("password") or ""
            confirm = request.form.get("confirm") or ""
            errors = {}
            if not name:
                errors["name"] = "Informe seu nome."
            if "@" not in email or "." not in email:
                errors["email"] = "Informe um e-mail válido."
            if len(password) < 6:
                errors["password"] = "A senha deve ter ao menos 6 caracteres."
            if password != confirm:
                errors["confirm"] = "As senhas não conferem."

            db = database.get_db()
            if not errors and db.execute(
                "SELECT 1 FROM users WHERE email = ?", (email,)
            ).fetchone():
                errors["email"] = "Já existe uma conta com esse e-mail."

            if errors:
                flash("Verifique os campos destacados.", "error")
                return render_template(
                    "registro.html", form={"name": name, "email": email}, errors=errors
                ), 400

            cur = db.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (name, email, generate_password_hash(password)),
            )
            db.commit()
            session.clear()
            session["user_id"] = cur.lastrowid
            flash("Conta criada! Comece preenchendo seu perfil financeiro.", "success")
            return redirect(url_for("perfil"))
        return render_template("registro.html", form={}, errors={})

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if g.user:
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            email = (request.form.get("email") or "").strip().lower()
            password = request.form.get("password") or ""
            db = database.get_db()
            user = db.execute(
                "SELECT * FROM users WHERE email = ?", (email,)
            ).fetchone()
            if user is None or not check_password_hash(user["password_hash"], password):
                flash("E-mail ou senha incorretos.", "error")
                return render_template("login.html", form={"email": email}), 400
            session.clear()
            session["user_id"] = user["id"]
            nxt = request.args.get("next")
            return redirect(nxt if nxt and nxt.startswith("/") else url_for("dashboard"))
        return render_template("login.html", form={})

    @app.route("/sair", methods=["POST"])
    def sair():
        session.clear()
        flash("Você saiu da sua conta.", "success")
        return redirect(url_for("home"))

    # --- App ---------------------------------------------------------------
    # Home (landing) publica em "/"; o app em si fica sob "/app".

    @app.route("/")
    def home():
        return render_template("home.html")

    @app.route("/app")
    def dashboard():
        db = database.get_db()
        data = reports.build_dashboard(db, g.user)
        return render_template("dashboard.html", active="dashboard", d=data)

    @app.route("/relatorios")
    def relatorios():
        db = database.get_db()
        today = date.today()
        # Periodo padrao: do 1o dia de 2 meses atras ate hoje (~3 meses).
        y, m = today.year, today.month - 2
        while m < 1:
            m += 12
            y -= 1
        default_start = date(y, m, 1).isoformat()

        start = request.args.get("start") or default_start
        end = request.args.get("end") or today.isoformat()
        _, e1 = parse_date(start)
        _, e2 = parse_date(end)
        if e1 or e2:
            start, end = default_start, today.isoformat()
        elif start > end:
            start, end = end, start

        data = reports.build_report(db, g.user, start, end)
        return render_template(
            "relatorios.html", active="relatorios", d=data, start=start, end=end
        )

    @app.route("/perfil", methods=["GET", "POST"])
    def perfil():
        db = database.get_db()
        main_goal = get_main_goal(db, uid())

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
                (form["name"], income, hours, limit, uid()),
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
                        (uid(), form["goal_name"], target, contribution or 0),
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
        db = database.get_db()
        # Filtros (querystring). Mes default = mes atual.
        f_month = request.args.get("month") or date.today().strftime("%Y-%m")
        f_type = request.args.get("type") or ""
        f_category = request.args.get("category_id") or ""

        sql = """SELECT t.*, c.name AS category_name, c.color AS category_color
                 FROM transactions t
                 LEFT JOIN categories c ON c.id = t.category_id
                 WHERE t.user_id = ?"""
        params = [uid()]
        if f_month:
            sql += " AND strftime('%Y-%m', t.date) = ?"
            params.append(f_month)
        if f_type in ("income", "expense"):
            sql += " AND t.type = ?"
            params.append(f_type)
        if f_category:
            sql += " AND t.category_id = ?"
            params.append(f_category)
        sql += " ORDER BY t.date DESC, t.id DESC"
        rows = db.execute(sql, params).fetchall()

        total_income = sum(r["amount"] for r in rows if r["type"] == "income")
        total_expense = sum(r["amount"] for r in rows if r["type"] == "expense")

        return render_template(
            "transacoes.html", active="transacoes",
            rows=rows, categories=get_categories(db),
            filters={"month": f_month, "type": f_type, "category_id": f_category},
            total_income=total_income, total_expense=total_expense,
            balance=total_income - total_expense,
        )

    @app.route("/transacoes/<int:tx_id>")
    def transacao_detalhe(tx_id):
        db = database.get_db()
        tx = db.execute(
            """SELECT t.*, c.name AS category_name, c.color AS category_color
               FROM transactions t
               LEFT JOIN categories c ON c.id = t.category_id
               WHERE t.id = ? AND t.user_id = ?""",
            (tx_id, uid()),
        ).fetchone()
        if tx is None:
            flash("Transação não encontrada.", "error")
            return redirect(url_for("transacoes"))

        # RealCost so faz sentido para despesas. Reusa o mesmo motor do simulador.
        analysis = None
        if tx["type"] == "expense" and g.user:
            main_goal = get_main_goal(db, uid())
            contribution = main_goal["monthly_contribution"] if main_goal else 0
            analysis = finance.analyze_purchase(
                amount=tx["amount"],
                installments=1,
                monthly_income=g.user["monthly_income"],
                monthly_hours=g.user["monthly_hours"],
                monthly_contribution=contribution,
            )
        return render_template(
            "transacao_detalhe.html", active="transacoes", tx=tx, rc=analysis,
        )

    def _validate_transaction(form):
        """Valida o dicionario do form. Retorna (dados, errors)."""
        errors = {}
        data = {}
        data["type"] = form.get("type")
        if data["type"] not in ("income", "expense"):
            errors["type"] = "Selecione receita ou despesa."
        data["description"] = (form.get("description") or "").strip()
        if not data["description"]:
            errors["description"] = "Informe uma descrição."

        amount, e = parse_decimal(form.get("amount"))
        if e:
            errors["amount"] = e
        elif not amount or amount <= 0:
            errors["amount"] = "O valor deve ser maior que zero."
        data["amount"] = amount

        d, e = parse_date(form.get("date"))
        if e:
            errors["date"] = e
        data["date"] = d

        cat = form.get("category_id") or None
        data["category_id"] = int(cat) if cat else None
        data["payment_method"] = (form.get("payment_method") or "").strip() or None
        data["is_recurring"] = 1 if form.get("is_recurring") else 0
        return data, errors

    @app.route("/transacoes/nova", methods=["GET", "POST"])
    def transacao_nova():
        db = database.get_db()
        if request.method == "POST":
            data, errors = _validate_transaction(request.form)
            if errors:
                flash("Verifique os campos destacados.", "error")
                return render_template(
                    "transacao_form.html", active="transacoes",
                    categories=get_categories(db), form=request.form,
                    errors=errors, mode="nova",
                ), 400
            db.execute(
                """INSERT INTO transactions
                   (user_id, type, description, category_id, amount, date,
                    payment_method, is_recurring)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (uid(), data["type"], data["description"],
                 data["category_id"], data["amount"], data["date"],
                 data["payment_method"], data["is_recurring"]),
            )
            db.commit()
            flash("Transação adicionada.", "success")
            return redirect(url_for("transacoes"))

        form = {"type": "expense", "date": date.today().strftime("%Y-%m-%d")}
        return render_template(
            "transacao_form.html", active="transacoes",
            categories=get_categories(db), form=form, errors={}, mode="nova",
        )

    @app.route("/transacoes/<int:tx_id>/editar", methods=["GET", "POST"])
    def transacao_editar(tx_id):
        db = database.get_db()
        tx = db.execute(
            "SELECT * FROM transactions WHERE id = ? AND user_id = ?",
            (tx_id, uid()),
        ).fetchone()
        if tx is None:
            flash("Transação não encontrada.", "error")
            return redirect(url_for("transacoes"))

        if request.method == "POST":
            data, errors = _validate_transaction(request.form)
            if errors:
                flash("Verifique os campos destacados.", "error")
                return render_template(
                    "transacao_form.html", active="transacoes",
                    categories=get_categories(db), form=request.form,
                    errors=errors, mode="editar", tx_id=tx_id,
                ), 400
            db.execute(
                """UPDATE transactions
                   SET type = ?, description = ?, category_id = ?, amount = ?,
                       date = ?, payment_method = ?, is_recurring = ?,
                       updated_at = CURRENT_TIMESTAMP
                   WHERE id = ? AND user_id = ?""",
                (data["type"], data["description"], data["category_id"],
                 data["amount"], data["date"], data["payment_method"],
                 data["is_recurring"], tx_id, uid()),
            )
            db.commit()
            flash("Transação atualizada.", "success")
            return redirect(url_for("transacoes"))

        return render_template(
            "transacao_form.html", active="transacoes",
            categories=get_categories(db), form=tx, errors={},
            mode="editar", tx_id=tx_id,
        )

    # --- Importacao CSV ---------------------------------------------------

    @app.route("/transacoes/importar", methods=["GET", "POST"])
    def transacao_importar():
        """Upload do CSV -> mostra preview. Confirmar grava em lote."""
        if request.method == "POST":
            file = request.files.get("file")
            if not file or not file.filename:
                flash("Selecione um arquivo CSV.", "error")
                return redirect(url_for("transacao_importar"))
            raw = file.read(2_000_000)  # 2 MB de teto
            rows, errors = parse_csv(raw)
            if not rows:
                for e in errors:
                    flash(e, "error")
                return redirect(url_for("transacao_importar"))
            # Guarda na sessao para o passo de confirmacao.
            session["import_preview"] = rows
            session["import_errors"] = errors
            return redirect(url_for("transacao_importar_preview"))
        return render_template("transacao_importar.html", active="transacoes")

    @app.route("/transacoes/importar/preview", methods=["GET", "POST"])
    def transacao_importar_preview():
        rows = session.get("import_preview") or []
        errors = session.get("import_errors") or []
        if not rows:
            return redirect(url_for("transacao_importar"))

        if request.method == "POST":
            db = database.get_db()
            inserted = 0
            for r in rows:
                db.execute(
                    """INSERT INTO transactions
                       (user_id, type, description, amount, date)
                       VALUES (?, ?, ?, ?, ?)""",
                    (uid(), r["type"], r["description"], r["amount"], r["date"]),
                )
                inserted += 1
            db.commit()
            session.pop("import_preview", None)
            session.pop("import_errors", None)
            flash(f"{inserted} transações importadas.", "success")
            return redirect(url_for("transacoes"))

        income_total = sum(r["amount"] for r in rows if r["type"] == "income")
        expense_total = sum(r["amount"] for r in rows if r["type"] == "expense")
        return render_template(
            "transacao_importar_preview.html", active="transacoes",
            rows=rows, errors=errors,
            income_total=income_total, expense_total=expense_total,
        )

    @app.route("/transacoes/<int:tx_id>/excluir", methods=["POST"])
    def transacao_excluir(tx_id):
        db = database.get_db()
        db.execute(
            "DELETE FROM transactions WHERE id = ? AND user_id = ?",
            (tx_id, uid()),
        )
        db.commit()
        flash("Transação excluída.", "success")
        return redirect(url_for("transacoes"))

    # --- Metas -------------------------------------------------------------

    def _goal_view(row):
        """Enriquece uma meta com progresso (%) e meses estimados."""
        target = row["target_amount"] or 0
        current = row["current_amount"] or 0
        contribution = row["monthly_contribution"] or 0
        progress = min((current / target * 100) if target > 0 else 0, 100)
        months = finance.goal_months_remaining(target, current, contribution)
        return {
            "id": row["id"],
            "name": row["name"],
            "target_amount": target,
            "current_amount": current,
            "monthly_contribution": contribution,
            "priority": row["priority"],
            "progress": progress,
            "remaining": max(target - current, 0),
            "months": months,
            "done": current >= target,
        }

    def _validate_goal(form):
        """Valida o form de meta. Retorna (dados, errors)."""
        errors, data = {}, {}
        data["name"] = (form.get("name") or "").strip()
        if not data["name"]:
            errors["name"] = "Informe o nome da meta."

        target, e = parse_decimal(form.get("target_amount"))
        if e:
            errors["target_amount"] = e
        elif not target or target <= 0:
            errors["target_amount"] = "O valor alvo deve ser maior que zero."
        data["target_amount"] = target

        current, e = parse_decimal(form.get("current_amount"))
        if e:
            errors["current_amount"] = e
        data["current_amount"] = current or 0

        contribution, e = parse_decimal(form.get("monthly_contribution"))
        if e:
            errors["monthly_contribution"] = e
        data["monthly_contribution"] = contribution or 0

        try:
            data["priority"] = int(form.get("priority") or 2)
        except ValueError:
            data["priority"] = 2
        return data, errors

    @app.route("/metas")
    def metas():
        db = database.get_db()
        rows = db.execute(
            "SELECT * FROM goals WHERE user_id = ? ORDER BY priority, id",
            (uid(),),
        ).fetchall()
        goals = [_goal_view(r) for r in rows]
        return render_template("metas.html", active="metas", goals=goals)

    @app.route("/metas/nova", methods=["GET", "POST"])
    def meta_nova():
        db = database.get_db()
        if request.method == "POST":
            data, errors = _validate_goal(request.form)
            if errors:
                flash("Verifique os campos destacados.", "error")
                return render_template(
                    "meta_form.html", active="metas",
                    form=request.form, errors=errors, mode="nova",
                ), 400
            db.execute(
                """INSERT INTO goals
                   (user_id, name, target_amount, current_amount,
                    monthly_contribution, priority)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (uid(), data["name"], data["target_amount"],
                 data["current_amount"], data["monthly_contribution"], data["priority"]),
            )
            db.commit()
            flash("Meta criada.", "success")
            return redirect(url_for("metas"))

        form = {"priority": 2, "current_amount": 0}
        return render_template(
            "meta_form.html", active="metas", form=form, errors={}, mode="nova",
        )

    @app.route("/metas/<int:goal_id>/editar", methods=["GET", "POST"])
    def meta_editar(goal_id):
        db = database.get_db()
        goal = db.execute(
            "SELECT * FROM goals WHERE id = ? AND user_id = ?",
            (goal_id, uid()),
        ).fetchone()
        if goal is None:
            flash("Meta não encontrada.", "error")
            return redirect(url_for("metas"))

        if request.method == "POST":
            data, errors = _validate_goal(request.form)
            if errors:
                flash("Verifique os campos destacados.", "error")
                return render_template(
                    "meta_form.html", active="metas",
                    form=request.form, errors=errors, mode="editar", goal_id=goal_id,
                ), 400
            db.execute(
                """UPDATE goals
                   SET name = ?, target_amount = ?, current_amount = ?,
                       monthly_contribution = ?, priority = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE id = ? AND user_id = ?""",
                (data["name"], data["target_amount"], data["current_amount"],
                 data["monthly_contribution"], data["priority"], goal_id, uid()),
            )
            db.commit()
            flash("Meta atualizada.", "success")
            return redirect(url_for("metas"))

        return render_template(
            "meta_form.html", active="metas", form=goal, errors={},
            mode="editar", goal_id=goal_id,
        )

    @app.route("/metas/<int:goal_id>/excluir", methods=["POST"])
    def meta_excluir(goal_id):
        db = database.get_db()
        db.execute(
            "DELETE FROM goals WHERE id = ? AND user_id = ?",
            (goal_id, uid()),
        )
        db.commit()
        flash("Meta excluída.", "success")
        return redirect(url_for("metas"))

    # --- Simulador "Posso comprar?" ---------------------------------------

    @app.route("/simulador", methods=["GET", "POST"])
    def simulador():
        db = database.get_db()
        categories = get_categories(db, "expense")
        result = None
        verdict = None
        form = {"installments": 1, "priority": "media"}

        if request.method == "POST":
            errors = {}
            form = {
                "item_name": (request.form.get("item_name") or "").strip(),
                "amount": request.form.get("amount", ""),
                "category_id": request.form.get("category_id") or "",
                "installments": request.form.get("installments", "1"),
                "priority": request.form.get("priority", "media"),
            }
            if not form["item_name"]:
                errors["item_name"] = "Informe o item."
            amount, e = parse_decimal(form["amount"])
            if e:
                errors["amount"] = e
            elif not amount or amount <= 0:
                errors["amount"] = "O valor deve ser maior que zero."
            try:
                installments = max(int(form["installments"]), 1)
            except (ValueError, TypeError):
                installments = 1

            if errors:
                flash("Verifique os campos destacados.", "error")
                return render_template(
                    "simulador.html", active="simulador",
                    categories=categories, form=form, errors=errors,
                    result=None, verdict=None,
                ), 400

            main_goal = get_main_goal(db, uid())
            contribution = main_goal["monthly_contribution"] if main_goal else 0
            user = g.user
            result = finance.analyze_purchase(
                amount=amount,
                installments=installments,
                monthly_income=user["monthly_income"] if user else 0,
                monthly_hours=user["monthly_hours"] if user else 0,
                monthly_contribution=contribution,
            )
            verdict = finance.purchase_verdict(result)

            # Guarda a simulacao (alimenta historico/relatorios futuros).
            db.execute(
                """INSERT INTO purchase_simulations
                   (user_id, item_name, amount, category_id, installments,
                    risk_level, result_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (uid(), form["item_name"], amount,
                 int(form["category_id"]) if form["category_id"] else None,
                 installments, result.risk, json.dumps(asdict(result))),
            )
            db.commit()

        return render_template(
            "simulador.html", active="simulador",
            categories=categories, form=form, errors={}, result=result, verdict=verdict,
        )

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
