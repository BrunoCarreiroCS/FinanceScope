from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
PDF_PATH = DOCS / "FinanceScope_Roadmap_Visual.pdf"

W, H = landscape(letter)

NAVY = colors.HexColor("#0B2545")
BLUE = colors.HexColor("#2563EB")
CYAN = colors.HexColor("#0891B2")
GREEN = colors.HexColor("#16A34A")
AMBER = colors.HexColor("#D97706")
RED = colors.HexColor("#DC2626")
PURPLE = colors.HexColor("#7C3AED")
SLATE = colors.HexColor("#475569")
GRAY = colors.HexColor("#64748B")
LIGHT = colors.HexColor("#F8FAFC")
BORDER = colors.HexColor("#CBD5E1")
INK = colors.HexColor("#111827")
FOOTER_LIGHT = colors.HexColor("#C7D2FE")


PHASES = [
    {
        "num": "01",
        "title": "Base visual e estrutura",
        "time": "Semana 1",
        "color": BLUE,
        "goal": "Criar a base navegavel do projeto.",
        "tasks": [
            "Estrutura Flask + templates",
            "Sidebar, header e grid do dashboard",
            "Tema visual desktop-first",
            "Home inicial e rotas principais",
        ],
        "done": "Aplicacao abre localmente e todas as telas base existem.",
    },
    {
        "num": "02",
        "title": "Perfil financeiro",
        "time": "Semana 1",
        "color": CYAN,
        "goal": "Guardar os dados que alimentam os calculos.",
        "tasks": [
            "Renda mensal",
            "Horas mensais",
            "Limite planejado",
            "Meta principal inicial",
        ],
        "done": "Perfil salva e valida valores antes do dashboard analitico.",
    },
    {
        "num": "03",
        "title": "Transacoes",
        "time": "Semana 2",
        "color": GREEN,
        "goal": "Registrar receitas e despesas reais ou demo.",
        "tasks": [
            "CRUD completo",
            "Categorias padrao",
            "Filtros por mes, tipo e categoria",
            "Dados de demonstracao",
        ],
        "done": "Usuario consegue consultar e editar lancamentos persistidos.",
    },
    {
        "num": "04",
        "title": "Dashboard",
        "time": "Semana 3",
        "color": AMBER,
        "goal": "Transformar dados em leitura rapida.",
        "tasks": [
            "Cards de resumo",
            "Grafico por categoria",
            "Evolucao mensal",
            "Ranking e alertas",
        ],
        "done": "Dashboard responde onde o dinheiro esta indo.",
    },
    {
        "num": "05",
        "title": "RealCost Engine",
        "time": "Semana 4",
        "color": PURPLE,
        "goal": "Implementar o diferencial central.",
        "tasks": [
            "Valor da hora",
            "Custo em horas",
            "Impacto na renda",
            "Atraso da meta e risco",
        ],
        "done": "Calculos isolados em utils/finance.py com testes.",
    },
    {
        "num": "06",
        "title": "Metas e simulador",
        "time": "Semana 5",
        "color": RED,
        "goal": "Ajudar o usuario a decidir antes de gastar.",
        "tasks": [
            "CRUD de metas",
            "Progresso e prazo estimado",
            "Simulador Posso Comprar?",
            "Mensagem analitica nao proibitiva",
        ],
        "done": "Compra simulada mostra horas, impacto, risco e atraso.",
    },
    {
        "num": "07",
        "title": "Polimento e GitHub",
        "time": "Semana 6",
        "color": SLATE,
        "goal": "Preparar o projeto para apresentacao.",
        "tasks": [
            "README completo",
            "Prints e GIF curto",
            "Deploy demonstravel",
            "Roadmap pos-MVP",
        ],
        "done": "Repositorio pronto para portfolio e entrevistas.",
    },
]


def wrap_text(text: str, max_chars: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        candidate = " ".join(current + [word])
        if len(candidate) > max_chars and current:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines


def draw_footer(c: canvas.Canvas, page: int, dark: bool = False) -> None:
    c.setFillColor(FOOTER_LIGHT if dark else GRAY)
    c.setFont("Helvetica", 8)
    c.drawString(0.45 * inch, 0.28 * inch, "FinanceScope - Roadmap Visual de Desenvolvimento")
    c.drawRightString(W - 0.45 * inch, 0.28 * inch, f"Pagina {page}")


def title(c: canvas.Canvas, text: str, subtitle: str | None = None) -> None:
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(0.55 * inch, H - 0.68 * inch, text)
    if subtitle:
        c.setFillColor(GRAY)
        c.setFont("Helvetica", 10)
        c.drawString(0.56 * inch, H - 0.9 * inch, subtitle)
    c.setStrokeColor(BORDER)
    c.line(0.55 * inch, H - 1.02 * inch, W - 0.55 * inch, H - 1.02 * inch)


def rounded_rect(c: canvas.Canvas, x, y, w, h, fill, stroke=BORDER, radius=10) -> None:
    c.setStrokeColor(stroke)
    c.setFillColor(fill)
    c.roundRect(x, y, w, h, radius, stroke=1, fill=1)


def card_header(c: canvas.Canvas, x, y, w, h, fill, radius=10) -> None:
    c.setFillColor(fill)
    c.roundRect(x, y, w, h, radius, stroke=0, fill=1)
    c.rect(x, y, w, h / 2, stroke=0, fill=1)


def cover(c: canvas.Canvas) -> None:
    c.setFillColor(NAVY)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 34)
    c.drawString(0.75 * inch, H - 1.55 * inch, "FinanceScope")
    c.setFont("Helvetica", 18)
    c.drawString(0.78 * inch, H - 1.95 * inch, "Roadmap visual de desenvolvimento")
    c.setFont("Helvetica", 11)
    c.drawString(
        0.79 * inch,
        H - 2.3 * inch,
        "Planejamento por fases para construir o MVP, validar o RealCost Engine e preparar o GitHub.",
    )
    x = 0.8 * inch
    y = H - 4.45 * inch
    c.setStrokeColor(colors.HexColor("#E2E8F0"))
    c.setLineWidth(1.2)
    c.line(x + 0.36 * inch, y + 0.36 * inch, x + 6 * 1.15 * inch + 0.36 * inch, y + 0.36 * inch)
    for phase in PHASES:
        c.setFillColor(phase["color"])
        c.roundRect(x, y, 0.72 * inch, 0.72 * inch, 12, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 13)
        c.drawCentredString(x + 0.36 * inch, y + 0.28 * inch, phase["num"])
        x += 1.15 * inch
    c.setFont("Helvetica", 10)
    c.drawString(0.8 * inch, 0.7 * inch, "Projeto beta | Nome final do site/produto ainda em aberto | Junho de 2026")


def macro_timeline(c: canvas.Canvas) -> None:
    title(c, "Mapa macro do MVP", "A ordem abaixo evita construir funcionalidades sofisticadas antes de existir dado confiavel.")
    card_w = 2.35 * inch
    card_h = 1.95 * inch
    gap = 0.18 * inch
    row_layout = [
        (PHASES[:4], 0.62 * inch, H - 3.23 * inch),
        (PHASES[4:], 1.88 * inch, 1.86 * inch),
    ]
    for row, x0, y in row_layout:
        for idx, phase in enumerate(row):
            x = x0 + idx * (card_w + gap)
            rounded_rect(c, x, y, card_w, card_h, colors.white, BORDER, 8)
            card_header(c, x, y + card_h - 0.42 * inch, card_w, 0.42 * inch, phase["color"], 8)
            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 9.5)
            c.drawString(x + 0.13 * inch, y + card_h - 0.26 * inch, f"{phase['num']} | {phase['time']}")
            c.setFillColor(INK)
            c.setFont("Helvetica-Bold", 9.2)
            ty = y + card_h - 0.7 * inch
            for line in wrap_text(phase["title"], 30):
                c.drawString(x + 0.13 * inch, ty, line)
                ty -= 0.15 * inch
            c.setFillColor(GRAY)
            c.setFont("Helvetica", 7.9)
            ty -= 0.04 * inch
            for line in wrap_text(phase["goal"], 38):
                c.drawString(x + 0.13 * inch, ty, line)
                ty -= 0.13 * inch
            c.setFillColor(INK)
            c.setFont("Helvetica", 7.4)
            ty -= 0.04 * inch
            for task in phase["tasks"][:3]:
                for line in wrap_text(f"- {task}", 40):
                    if ty < y + 0.22 * inch:
                        break
                    c.drawString(x + 0.14 * inch, ty, line)
                    ty -= 0.12 * inch

    c.setFillColor(LIGHT)
    c.roundRect(0.65 * inch, 0.58 * inch, W - 1.3 * inch, 0.86 * inch, 10, stroke=1, fill=1)
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(0.86 * inch, 1.14 * inch, "Trilha de valor")
    c.setFillColor(INK)
    c.setFont("Helvetica", 8.3)
    c.drawString(
        0.86 * inch,
        0.9 * inch,
        "Base navegavel -> dados financeiros -> dashboard -> RealCost -> decisao de compra -> portfolio apresentavel.",
    )
    c.setFillColor(GRAY)
    c.setFont("Helvetica", 7.5)
    c.drawString(0.86 * inch, 0.7 * inch, "Nao avance uma fase se o criterio de aceite anterior ainda estiver quebrado.")


def phase_detail_page(c: canvas.Canvas, start: int, page_title: str) -> None:
    title(c, page_title, "Cada card funciona como uma ordem de servico para desenvolvimento.")
    card_w = 3.25 * inch
    card_h = 2.05 * inch
    if start == 6:
        card_w = 3.75 * inch
        card_h = 2.35 * inch
        positions = [(3.62 * inch, H - 4.35 * inch)]
    else:
        positions = [
            (0.65 * inch, H - 3.2 * inch),
            (4.05 * inch, H - 3.2 * inch),
            (7.45 * inch, H - 3.2 * inch),
            (0.65 * inch, H - 5.55 * inch),
            (4.05 * inch, H - 5.55 * inch),
            (7.45 * inch, H - 5.55 * inch),
        ]
    for phase, (x, y) in zip(PHASES[start:start + 6], positions):
        rounded_rect(c, x, y, card_w, card_h, colors.white, BORDER, 10)
        card_header(c, x, y + card_h - 0.38 * inch, card_w, 0.38 * inch, phase["color"], 10)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x + 0.12 * inch, y + card_h - 0.24 * inch, f"Fase {phase['num']} - {phase['time']}")
        c.setFillColor(NAVY)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(x + 0.12 * inch, y + card_h - 0.62 * inch, phase["title"])
        c.setFillColor(GRAY)
        c.setFont("Helvetica", 8)
        yy = y + card_h - 0.88 * inch
        for line in wrap_text(phase["goal"], 54):
            c.drawString(x + 0.12 * inch, yy, line)
            yy -= 0.13 * inch
        yy -= 0.05 * inch
        c.setFillColor(INK)
        c.setFont("Helvetica", 7.6)
        for task in phase["tasks"]:
            for line in wrap_text(f"- {task}", 56):
                c.drawString(x + 0.14 * inch, yy, line)
                yy -= 0.12 * inch
        c.setFillColor(phase["color"])
        c.setFont("Helvetica-Bold", 7.4)
        c.drawString(x + 0.12 * inch, y + 0.16 * inch, "PRONTO QUANDO:")
        c.setFillColor(INK)
        c.setFont("Helvetica", 7.2)
        for line in wrap_text(phase["done"], 50):
            c.drawString(x + 1.12 * inch, y + 0.16 * inch, line)


def product_visual(c: canvas.Canvas) -> None:
    title(c, "Projeto visual do produto", "Direcao de interface para o FinanceScope beta: dashboard SaaS, claro, analitico e demonstravel.")
    x = 0.7 * inch
    y = 0.8 * inch
    panel_w = W - 1.4 * inch
    panel_h = H - 2.15 * inch
    rounded_rect(c, x, y, panel_w, panel_h, colors.white, BORDER, 12)

    sidebar_w = 1.5 * inch
    c.setFillColor(NAVY)
    c.roundRect(x, y, sidebar_w, panel_h, 12, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x + 0.18 * inch, y + panel_h - 0.42 * inch, "FinanceScope")
    c.setFont("Helvetica", 8)
    nav_items = ["Dashboard", "Transacoes", "Metas", "Simulador", "Relatorios"]
    yy = y + panel_h - 0.9 * inch
    for item in nav_items:
        c.setFillColor(colors.HexColor("#123A63") if item == "Dashboard" else NAVY)
        c.roundRect(x + 0.14 * inch, yy - 0.07 * inch, sidebar_w - 0.28 * inch, 0.28 * inch, 5, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.drawString(x + 0.26 * inch, yy, item)
        yy -= 0.43 * inch

    content_x = x + sidebar_w + 0.32 * inch
    content_w = panel_w - sidebar_w - 0.58 * inch
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 15)
    c.drawString(content_x, y + panel_h - 0.45 * inch, "Dashboard principal")
    c.setFillColor(GRAY)
    c.setFont("Helvetica", 8)
    c.drawRightString(x + panel_w - 0.3 * inch, y + panel_h - 0.43 * inch, "Filtro: Junho/2026")

    card_y = y + panel_h - 1.55 * inch
    card_w = (content_w - 0.45 * inch) / 4
    cards = [
        ("Renda", "R$ 3.200", GREEN),
        ("Gastos", "R$ 1.860", RED),
        ("Saldo", "R$ 1.340", BLUE),
        ("Maior vazamento", "Delivery", AMBER),
    ]
    for idx, (label, value, color) in enumerate(cards):
        cx = content_x + idx * (card_w + 0.15 * inch)
        rounded_rect(c, cx, card_y, card_w, 0.72 * inch, LIGHT, BORDER, 8)
        c.setFillColor(color)
        c.circle(cx + 0.18 * inch, card_y + 0.51 * inch, 0.055 * inch, stroke=0, fill=1)
        c.setFillColor(GRAY)
        c.setFont("Helvetica", 7.5)
        c.drawString(cx + 0.33 * inch, card_y + 0.47 * inch, label)
        c.setFillColor(INK)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(cx + 0.16 * inch, card_y + 0.18 * inch, value)

    chart_y = y + 1.85 * inch
    chart_h = 1.75 * inch
    rounded_rect(c, content_x, chart_y, content_w * 0.58, chart_h, colors.white, BORDER, 8)
    rounded_rect(c, content_x + content_w * 0.61, chart_y, content_w * 0.39, chart_h, colors.white, BORDER, 8)
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(content_x + 0.16 * inch, chart_y + chart_h - 0.28 * inch, "Gastos por categoria")
    c.drawString(content_x + content_w * 0.61 + 0.16 * inch, chart_y + chart_h - 0.28 * inch, "Alertas RealCost")
    bars = [(0.75, BLUE), (0.52, GREEN), (0.38, AMBER), (0.25, RED)]
    by = chart_y + 0.3 * inch
    for idx, (pct, color) in enumerate(bars):
        c.setFillColor(colors.HexColor("#E2E8F0"))
        c.rect(content_x + 0.2 * inch, by + idx * 0.28 * inch, 2.9 * inch, 0.12 * inch, stroke=0, fill=1)
        c.setFillColor(color)
        c.rect(content_x + 0.2 * inch, by + idx * 0.28 * inch, 2.9 * inch * pct, 0.12 * inch, stroke=0, fill=1)
    alert_x = content_x + content_w * 0.61 + 0.18 * inch
    alerts = [
        "Compra X = 18h40 de trabalho",
        "Meta principal atrasa 1,2 mes",
        "Ritmo atual pode estourar limite",
    ]
    ay = chart_y + chart_h - 0.62 * inch
    c.setFillColor(INK)
    c.setFont("Helvetica", 8)
    for item in alerts:
        c.drawString(alert_x, ay, f"- {item}")
        ay -= 0.28 * inch

    c.setFillColor(LIGHT)
    c.roundRect(content_x, y + 0.45 * inch, content_w, 0.86 * inch, 8, stroke=1, fill=1)
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(content_x + 0.18 * inch, y + 1.04 * inch, "Principio de UX")
    c.setFillColor(INK)
    c.setFont("Helvetica", 8)
    c.drawString(
        content_x + 0.18 * inch,
        y + 0.76 * inch,
        "Cada tela deve responder uma pergunta: para onde foi o dinheiro, qual e o risco, e o que muda se o usuario decidir comprar ou cortar.",
    )


def weekly_plan(c: canvas.Canvas) -> None:
    title(c, "Planejamento semana a semana", "Um roteiro pratico para transformar o escopo em entregas verificaveis.")
    rows = [
        ["Semana", "Foco", "Entregas", "Nao fazer ainda"],
        ["1", "Base + perfil", "Rotas, layout, telas vazias, perfil financeiro salvo.", "Login, score, relatorios longos."],
        ["2", "Transacoes", "CRUD, categorias padrao, filtros e SQLite consistente.", "Graficos complexos antes de dados confiaveis."],
        ["3", "Dashboard", "Cards, Chart.js, ranking, previsao e alertas simples.", "Assinaturas avancadas e exportacao."],
        ["4", "RealCost", "utils/finance.py, formulas, testes unitarios e textos explicativos.", "Regras opacas ou sem formula visivel."],
        ["5", "Metas + simulador", "Metas, progresso, prazo, simulador Posso Comprar?.", "Recomendacao financeira personalizada."],
        ["6", "Entrega GitHub", "README, prints, GIF, dados demo, deploy e revisao.", "Novas features grandes sem polimento."],
    ]
    x = 0.65 * inch
    y = H - 5.95 * inch
    col_w = [0.75 * inch, 1.55 * inch, 5.0 * inch, 3.0 * inch]
    row_h = 0.57 * inch
    for r, row in enumerate(rows):
        yy = y + (len(rows) - 1 - r) * row_h
        c.setFillColor(LIGHT if r else NAVY)
        c.rect(x, yy, sum(col_w), row_h, stroke=1, fill=1)
        xx = x
        for idx, cell in enumerate(row):
            c.setStrokeColor(BORDER)
            c.rect(xx, yy, col_w[idx], row_h, stroke=1, fill=0)
            c.setFillColor(colors.white if r == 0 else INK)
            c.setFont("Helvetica-Bold" if r == 0 or idx < 2 else "Helvetica", 8)
            lines = wrap_text(cell, int(col_w[idx] / inch * 17))
            text_y = yy + row_h - 0.18 * inch
            for line in lines[:3]:
                c.drawString(xx + 0.08 * inch, text_y, line)
                text_y -= 0.13 * inch
            xx += col_w[idx]


def acceptance_board(c: canvas.Canvas) -> None:
    title(c, "Quadro de aceite do MVP", "Use esta pagina como checklist final antes de publicar o repositorio.")
    columns = [
        ("Dados", BLUE, ["Perfil financeiro salvo", "SQLite com tabelas centrais", "Categorias padrao", "Dados demo realistas"]),
        ("Analise", PURPLE, ["RealCost testado", "Dashboard com 2 graficos", "Previsao de fechamento", "Risco explicado"]),
        ("Experiencia", GREEN, ["Fluxo claro por tela", "Mensagens nao proibitivas", "Desktop-first polido", "Estados vazios tratados"]),
        ("Portfolio", AMBER, ["README completo", "Prints e GIF", "Deploy demonstravel", "Roadmap pos-MVP"]),
    ]
    margin_x = 0.62 * inch
    gap = 0.22 * inch
    y = H - 5.78 * inch
    col_w = (W - 2 * margin_x - 3 * gap) / 4
    for idx, (name, color, items) in enumerate(columns):
        x = margin_x + idx * (col_w + gap)
        rounded_rect(c, x, y, col_w, 4.55 * inch, colors.white, BORDER, 12)
        card_header(c, x, y + 4.05 * inch, col_w, 0.5 * inch, color, 12)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(x + col_w / 2, y + 4.22 * inch, name)
        c.setFillColor(INK)
        c.setFont("Helvetica", 8.5)
        yy = y + 3.65 * inch
        for item in items:
            c.setStrokeColor(color)
            c.rect(x + 0.16 * inch, yy - 0.02 * inch, 0.14 * inch, 0.14 * inch, stroke=1, fill=0)
            text_x = x + 0.38 * inch
            line_y = yy
            for line in wrap_text(item, 28):
                c.drawString(text_x, line_y, line)
                line_y -= 0.13 * inch
            yy -= 0.48 * inch


def github_release(c: canvas.Canvas) -> None:
    title(c, "Entrega final para GitHub", "O objetivo e parecer projeto real, nao apenas exercicio de CRUD.")
    lanes = [
        ("README", BLUE, ["Resumo do problema", "Diferencial RealCost", "Stack e arquitetura", "Como rodar localmente"]),
        ("Demonstracao", CYAN, ["Print do dashboard", "GIF do simulador", "Dados demo", "Deploy ou video curto"]),
        ("Qualidade", GREEN, ["Testes do RealCost", "Validacoes basicas", "Sem dados sensiveis", "Aviso educacional"]),
        ("Evolucao", PURPLE, ["Login", "CSV", "Assinaturas completas", "Relatorios PDF e mobile"]),
    ]
    x = 0.75 * inch
    y = H - 2.05 * inch
    row_w = W - 1.5 * inch
    label_w = 1.55 * inch
    item_start = x + label_w + 0.32 * inch
    item_gap = (row_w - label_w - 0.45 * inch) / 4
    for idx, (name, color, items) in enumerate(lanes):
        row_y = y - idx * 1.05 * inch
        rounded_rect(c, x, row_y, row_w, 0.78 * inch, colors.white, BORDER, 8)
        c.setFillColor(color)
        c.roundRect(x, row_y, label_w, 0.78 * inch, 8, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 10.5)
        c.drawCentredString(x + label_w / 2, row_y + 0.29 * inch, name)
        c.setFillColor(INK)
        c.setFont("Helvetica", 8.6)
        for item_idx, item in enumerate(items):
            xx = item_start + item_idx * item_gap
            yy = row_y + 0.34 * inch
            for line in wrap_text(item, 24):
                c.drawString(xx, yy, line)
                yy -= 0.13 * inch
    c.setFillColor(LIGHT)
    c.roundRect(0.8 * inch, 0.85 * inch, W - 1.6 * inch, 1.0 * inch, 10, stroke=1, fill=1)
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(1.0 * inch, 1.5 * inch, "Regra final")
    c.setFillColor(INK)
    c.setFont("Helvetica", 9)
    c.drawString(
        1.0 * inch,
        1.18 * inch,
        "Publique somente quando o usuario conseguir ver dados demo, simular uma compra e entender o impacto em horas, renda e meta.",
    )


def main() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(PDF_PATH), pagesize=landscape(letter))
    pages = [
        cover,
        macro_timeline,
        product_visual,
        lambda cc: phase_detail_page(cc, 0, "Fases 1 a 6 em detalhe"),
        lambda cc: phase_detail_page(cc, 6, "Fase 7 em detalhe"),
        weekly_plan,
        acceptance_board,
        github_release,
    ]
    for idx, draw in enumerate(pages, start=1):
        draw(c)
        draw_footer(c, idx, dark=(idx == 1))
        c.showPage()
    c.save()
    print(PDF_PATH)


if __name__ == "__main__":
    main()
