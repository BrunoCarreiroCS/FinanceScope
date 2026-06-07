<div align="center">

# FinanceScope

**Entenda seu dinheiro. Decida melhor. Viva leve.**

Sistema web de gestão financeira pessoal com foco em **decisão**, não só em
registro. Em vez de mostrar onde o dinheiro foi, ajuda a responder *"posso
comprar isso?"* — traduzindo cada gasto em **horas de trabalho**, **impacto na
renda** e **atraso nas metas**.

[🌐 Demo online](https://brunoso.pythonanywhere.com)  ·  conta demo: `demo@financescope.app` / `demo1234`

</div>

---

## ✨ O diferencial: RealCost Engine

A maioria dos apps de finanças responde *"para onde o dinheiro foi?"*. Eles te
mostram um gráfico no fim do mês — quando o dano já está feito.

O FinanceScope responde a pergunta que importa **antes** de você gastar:
**"vale a pena?"**

Cada despesa é traduzida em três dimensões reais:

- 🕒 **Tempo de trabalho** — um tênis de R$ 350 custa 18h40 de trabalho
- 💰 **% da sua renda** — quanto pesa no seu mês
- 🎯 **Atraso na meta** — quantos meses de aporte essa compra consome

E o simulador entrega um **veredito** claro: 🟢 *Vale a pena* · 🟡 *Melhor
esperar* · 🔴 *Não compre agora* — sempre explicando o porquê. Sugere, não
manda.

---

## 🚀 Funcionalidades

| Módulo | O que faz |
|---|---|
| 🔐 **Login multiusuário** | Cadastro/login com senha hash (scrypt), proteção CSRF, sessões isoladas |
| 📊 **Dashboard** | Receitas, despesas, saldo, **previsão de fechamento**, alertas de risco, gráficos (Chart.js) |
| 💸 **Transações** | CRUD completo com filtros (mês/tipo/categoria), categorias coloridas |
| 📥 **Importação CSV** | Parser tolerante (vírgula/ponto, BR/ISO, separador `,` ou `;`) com pré-visualização |
| 🧮 **RealCost** | Tradução de cada gasto em horas, % da renda e atraso na meta |
| 🎯 **Metas** | Progresso, prazo estimado, prioridades, CRUD |
| 🛒 **Simulador "Posso comprar?"** | Impacto antes de comprar + **veredito de decisão** |
| 📈 **Relatórios** | Análise por período, exportação para PDF (impressão otimizada) |
| 💡 **Tooltips didáticos** | Cada termo financeiro com explicação ao passar o mouse |

---

## 🛠️ Tecnologias

| Camada | Stack |
|---|---|
| **Backend** | Python 3.11 · Flask 3 |
| **Persistência** | SQLite (1 arquivo, sem servidor) |
| **Segurança** | Werkzeug (hash de senha scrypt) · sessões assinadas · token CSRF · cookies `HttpOnly`/`SameSite`/`Secure` |
| **Frontend** | Jinja2 · CSS puro (sem framework) · Inter (Google Fonts) · Chart.js (CDN) |
| **Testes** | pytest (54 testes — RealCost, relatórios, autenticação, CSV, CSRF) |
| **Deploy** | PythonAnywhere (HTTPS, banco persistente, gratuito) |

> **Por que sem framework de CSS?** Tudo é CSS próprio (≈ 800 linhas) para
> demonstrar domínio de fundamentos: variáveis, grid, flex, dark mode, estados
> de hover/focus, responsivo e media queries (inclusive um tema claro para
> impressão do PDF).

---

## 🧮 As fórmulas (transparência total)

Todas centralizadas em [`app/utils/finance.py`](app/utils/finance.py) e
cobertas por testes em [`app/tests/test_finance.py`](app/tests/test_finance.py):

| Cálculo | Fórmula |
|---|---|
| Valor da hora | `renda_mensal / horas_mensais` |
| Custo em horas | `valor / valor_da_hora` |
| Impacto na renda | `(valor / renda_mensal) × 100` |
| Saldo do mês | `receitas − despesas` |
| Previsão de fechamento | `média_diária_despesas × dias_do_mês` |
| Tempo da meta | `(alvo − atual) / aporte_mensal` |
| Atraso da meta | `valor_compra / aporte_mensal` |

O app mostra as fórmulas perto dos resultados — porque transparência aumenta
confiança e ensina enquanto usa.

---

## 🎨 Identidade visual

Inspirada na união de duas referências bem conhecidas:

- **Binance** — dark profissional, números grandes tabulares, palette verde
  ("alta") / vermelho ("baixa") / dourado (atenção)
- **Organizze** — leveza, círculos de categoria coloridos, linguagem amigável,
  tooltips didáticos

O resultado é um SaaS sério mas **acolhedor** — pra quem leva dinheiro a sério
sem perder o lado humano.

---

## ▶️ Como usar

### Online (sem instalar nada)

1. Acesse **[a demo](https://brunoso.pythonanywhere.com)**
2. Entre com `demo@financescope.app` / `demo1234` **ou** crie sua conta
3. Preencha seu perfil (renda, horas mensais, meta principal)
4. Cadastre transações *ou* importe um extrato CSV
5. Veja o dashboard, abra **Relatórios** ou teste o **Simulador**

### Localmente

```bash
cd app
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate        # Linux/Mac

pip install -r requirements.txt
flask init-db                    # cria as tabelas
flask seed-demo                  # opcional: cria usuário demo
flask run
```

Acesse **http://127.0.0.1:5000**.

### Rodar os testes

```bash
cd app
pytest
```

### Deploy gratuito (PythonAnywhere)

Guia passo a passo em **[`DEPLOY.md`](DEPLOY.md)** — hospedagem grátis, com
HTTPS e banco persistente.

---

## 🗂️ Arquitetura

```
app/
├── app.py                  # rotas, autenticação, regras de negócio
├── database.py             # conexão SQLite + flask init-db
├── schema.sql              # users, categories, transactions, goals, simulations
├── seeds.py                # flask seed-demo (usuário + dados de exemplo)
├── utils/
│   ├── finance.py          # RealCost Engine (fórmulas, risco, veredito)
│   ├── reports.py          # agregações: dashboard e relatórios por período
│   ├── csv_import.py       # parser flexível de extratos
│   └── forms.py            # parsing/validação de inputs
├── templates/              # Jinja2 (landing, auth, app)
├── static/                 # CSS, JS, favicon
└── tests/                  # pytest (54 testes)
```

**Padrões aplicados:** factory pattern (`create_app`), context managers (Flask
`g`), validação em camadas (HTML5 + Python + constraints SQL), POST/Redirect/GET,
mensagens flash, tratamento de divisão por zero, sanitização contra
SQL-injection (parâmetros), CSRF, hash de senha, e separação clara entre
camada de dados, regras e apresentação.

---

## 🛤️ Roadmap de fases (como foi construído)

Projeto desenvolvido por fases, com commits organizados:

| Fase | Entrega |
|---|---|
| 1 | Estrutura Flask, layout dark, navegação |
| 2 | Perfil financeiro (renda, horas, limite, meta) |
| 3 | CRUD de transações com filtros |
| 4 | Dashboard com cards, gráficos Chart.js e alertas |
| 5 | RealCost Engine em detalhes de despesa |
| 6 | Metas (progresso/prazo) e Simulador "Posso comprar?" com veredito |
| 7 | Login multiusuário, polimento, deploy |
| ➕ | CSRF, relatórios por período + PDF, importação CSV, empty states |

**Tempo de desenvolvimento:** desenvolvido em sprints curtos, partindo de um
plano técnico documentado em [`docs/`](docs/) (PDF e DOCX) e evoluindo por
*pull requests* mentais — uma fase por vez, sempre com testes.

---

## 🔮 Roadmap futuro

- 🤖 **Chatbot com IA** — assistente conversacional sobre os próprios dados:
  *"Quanto eu gastei com lazer este mês?"* · *"Quanto tempo até atingir a
  meta?"* · *"O que devo cortar primeiro?"*
- 📊 **Score financeiro** evolutivo (saúde do mês)
- 🔁 **Assinaturas** (custo anual de recorrentes)
- 📱 **App mobile** / responsivo dedicado
- 🏦 **Integração bancária** (Open Finance / Pluggy)
- 📤 **Exportação CSV** dos próprios dados

---

## ⚖️ Aviso

As análises do FinanceScope são **estimativas educacionais** baseadas nos dados
que você informa. **Não substituem** orientação financeira profissional.

O produto **sugere**, não impõe. Frases como "estimativa", "no ritmo atual",
"com base nos seus dados" são propositais — você é quem decide.

---

<div align="center">

**Bruno Carreiro dos Santos**
[GitHub](https://github.com/BrunoCarreiroCS) · [LinkedIn](#) · [E-mail](mailto:karsario31@gmail.com)

© 2026 FinanceScope · Todos os direitos reservados.

</div>
