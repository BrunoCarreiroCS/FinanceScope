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
isso?"** — mostrando o custo real em tempo de trabalho e o impacto nas suas
metas.

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

- **Flask** — rotas, regras de negócio
- **SQLite** — persistência local
- **Jinja2 + CSS próprio** — layout SaaS dark/verde, desktop-first
- **Chart.js** — gráficos do dashboard
- **pytest** — testes do RealCost Engine

## Funcionalidades (MVP)

- [x] Estrutura base, layout e navegação (Fase 1)
- [x] RealCost Engine com testes (Fase 5, adiantado)
- [x] Perfil financeiro (Fase 2)
- [x] CRUD de transações (Fase 3)
- [ ] Dashboard e gráficos (Fase 4)
- [ ] Metas e simulador "Posso Comprar?" (Fase 6)
- [ ] Polimento, dados demo e deploy (Fase 7)

## Como rodar

```bash
cd app
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt

# cria o banco SQLite (perfil + categorias iniciais)
flask init-db

# inicia o servidor
flask run
```

Acesse http://127.0.0.1:5000

### Rodar os testes

```bash
cd app
pytest
```

## Roadmap (pós-MVP)

Login e multiusuário · importação CSV · score financeiro · assinaturas
completas · relatórios PDF · responsividade mobile.

---

Projeto desenvolvido por fases, com commits organizados para demonstrar o
processo. Veja o plano completo em [`docs/`](docs/).
