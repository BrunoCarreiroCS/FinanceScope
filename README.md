# FinanceScope

Sistema web **desktop-first** de gestão financeira pessoal com foco em
**dashboard, diagnóstico e simulação de decisões**.

O diferencial é o **RealCost Engine**: ele traduz cada gasto em **horas de
trabalho**, **impacto na renda**, **risco de fechamento do mês** e **atraso em
metas** — para você decidir antes de gastar, não depois.

> As análises são estimativas baseadas nos dados informados e **não substituem
> planejamento financeiro profissional**.

---

## O problema

Apps de finanças mostram *onde* o dinheiro foi, mas não ajudam a *decidir* antes
da compra. FinanceScope responde a pergunta que importa: **"posso comprar
isso?"** — mostrando o custo real em tempo de trabalho, o impacto nas metas e um
**veredito** (vale a pena / melhor esperar / não compre agora).

## Diferencial RealCost

| Cálculo | Fórmula |
|---|---|
| Valor da hora | `renda_mensal / horas_mensais` |
| Custo em horas | `valor / valor_da_hora` |
| Impacto na renda | `(valor / renda_mensal) * 100` |
| Saldo do mês | `total_receitas - total_despesas` |
| Previsão de fechamento | `media_diaria_despesas * dias_do_mes` |
| Tempo da meta | `(valor_alvo - valor_atual) / aporte_mensal` |
| Atraso da meta | `valor_compra / aporte_mensal` |

Todas centralizadas em [`app/utils/finance.py`](app/utils/finance.py) e cobertas
por testes em [`app/tests/test_finance.py`](app/tests/test_finance.py).

## Stack

- **Flask** — rotas, regras de negócio e autenticação por sessão
- **SQLite** — persistência (um arquivo por instalação, em `app/instance/`)
- **Werkzeug** — hash de senhas (scrypt/pbkdf2)
- **Jinja2 + CSS próprio** — layout SaaS dark/verde (Organizze × Binance), desktop-first
- **Chart.js** — gráficos do dashboard
- **pytest** — testes do RealCost Engine, dos relatórios e da autenticação

## Funcionalidades

- [x] Tela de boas-vindas (landing) e navegação
- [x] **Login multiusuário** (cadastro, login, logout) — cada um vê só os seus dados
- [x] Perfil financeiro (renda, horas, limite, meta principal)
- [x] CRUD de transações com filtros (mês, tipo, categoria)
- [x] Dashboard com cards, gráficos (Chart.js) e alertas de risco
- [x] **RealCost** em detalhes de despesa (custo em horas, % da renda, risco)
- [x] Metas com progresso e prazo estimado
- [x] Simulador "Posso comprar?" com **veredito de decisão**
- [x] Tooltips de ajuda (ícone "i") em todas as telas
- [x] Dados de demonstração + testes automatizados

## Como rodar

```bash
cd app
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt

# cria o banco SQLite (categorias padrão)
flask init-db

# opcional: cria um usuário demo já com dados de exemplo
flask seed-demo

# inicia o servidor
flask run
```

Acesse **http://127.0.0.1:5000** — a raiz abre a tela de boas-vindas; crie sua
conta em **Criar conta** e o app fica em `/app`.

### Conta de demonstração

Se você rodou `flask seed-demo`:

```
E-mail: demo@financescope.app
Senha:  demo1234
```

### Rodar os testes

```bash
cd app
pytest
```

### Configuração de produção

Defina uma chave de sessão forte via variável de ambiente:

```bash
export SECRET_KEY="uma-chave-bem-aleatoria"   # Windows: set SECRET_KEY=...
```

## Arquitetura

```
app/
├── app.py            # rotas, autenticação e regras de negócio
├── database.py       # conexão SQLite + comando init-db
├── schema.sql        # tabelas: users, categories, transactions, goals, purchase_simulations
├── seeds.py          # comando seed-demo (usuário + dados de exemplo)
├── utils/
│   ├── finance.py    # RealCost Engine (fórmulas, risco, veredito)
│   ├── reports.py    # agregações do dashboard
│   └── forms.py      # parsing/validação de formulários
├── templates/        # Jinja2 (landing, auth, app)
├── static/           # CSS, JS, favicon
└── tests/            # pytest (finance, reports, auth)
```

## Roadmap (pós-MVP)

Importação CSV de extratos · relatórios por período + exportação PDF · score
financeiro · assinaturas (custo anual recorrente) · responsividade mobile.

---

Projeto desenvolvido por fases, com commits organizados para demonstrar o
processo. Veja o plano completo em [`docs/`](docs/).
