"""Transacoes: CRUD, detalhe com RealCost e importacao de CSV."""
from datetime import date

from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

import database
from helpers import get_categories, get_main_goal, uid
from utils import finance
from utils.csv_import import parse_csv
from utils.forms import parse_date, parse_decimal

bp = Blueprint("transactions", __name__)


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


@bp.route("/transacoes")
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


@bp.route("/transacoes/<int:tx_id>")
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
        return redirect(url_for("transactions.transacoes"))

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


@bp.route("/transacoes/nova", methods=["GET", "POST"])
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
        return redirect(url_for("transactions.transacoes"))

    form = {"type": "expense", "date": date.today().strftime("%Y-%m-%d")}
    return render_template(
        "transacao_form.html", active="transacoes",
        categories=get_categories(db), form=form, errors={}, mode="nova",
    )


@bp.route("/transacoes/<int:tx_id>/editar", methods=["GET", "POST"])
def transacao_editar(tx_id):
    db = database.get_db()
    tx = db.execute(
        "SELECT * FROM transactions WHERE id = ? AND user_id = ?",
        (tx_id, uid()),
    ).fetchone()
    if tx is None:
        flash("Transação não encontrada.", "error")
        return redirect(url_for("transactions.transacoes"))

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
        return redirect(url_for("transactions.transacoes"))

    return render_template(
        "transacao_form.html", active="transacoes",
        categories=get_categories(db), form=tx, errors={},
        mode="editar", tx_id=tx_id,
    )


@bp.route("/transacoes/importar", methods=["GET", "POST"])
def transacao_importar():
    """Upload do CSV -> mostra preview. Confirmar grava em lote."""
    if request.method == "POST":
        file = request.files.get("file")
        if not file or not file.filename:
            flash("Selecione um arquivo CSV.", "error")
            return redirect(url_for("transactions.transacao_importar"))
        raw = file.read(2_000_000)  # 2 MB de teto
        rows, errors = parse_csv(raw)
        if not rows:
            for e in errors:
                flash(e, "error")
            return redirect(url_for("transactions.transacao_importar"))
        # Guarda na sessao para o passo de confirmacao.
        session["import_preview"] = rows
        session["import_errors"] = errors
        return redirect(url_for("transactions.transacao_importar_preview"))
    return render_template("transacao_importar.html", active="transacoes")


@bp.route("/transacoes/importar/preview", methods=["GET", "POST"])
def transacao_importar_preview():
    rows = session.get("import_preview") or []
    errors = session.get("import_errors") or []
    if not rows:
        return redirect(url_for("transactions.transacao_importar"))

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
        return redirect(url_for("transactions.transacoes"))

    income_total = sum(r["amount"] for r in rows if r["type"] == "income")
    expense_total = sum(r["amount"] for r in rows if r["type"] == "expense")
    return render_template(
        "transacao_importar_preview.html", active="transacoes",
        rows=rows, errors=errors,
        income_total=income_total, expense_total=expense_total,
    )


@bp.route("/transacoes/<int:tx_id>/excluir", methods=["POST"])
def transacao_excluir(tx_id):
    db = database.get_db()
    db.execute(
        "DELETE FROM transactions WHERE id = ? AND user_id = ?",
        (tx_id, uid()),
    )
    db.commit()
    flash("Transação excluída.", "success")
    return redirect(url_for("transactions.transacoes"))
