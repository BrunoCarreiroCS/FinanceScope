# FinanceScope — servidores MCP

Dois servidores [MCP](https://modelcontextprotocol.io) para o FinanceScope:

| Servidor | Arquivo | Precisa de dados? |
|---|---|---|
| **RealCost (engine)** | `server.py` | Não — stateless, você informa os números |
| **Consultor (dados reais)** | `consultor_server.py` | Sim — lê suas finanças via API com token |

---

## 1) `financescope_mcp` — RealCost via MCP (stateless)

Expõe o **RealCost Engine** como ferramentas para um assistente (ex.: Claude Desktop).

É **stateless**: não acessa banco nem dados de usuário. Quem fornece os números
(renda, horas, aporte) é a própria conversa. Reusa `app/utils/finance.py` — a mesma
lógica coberta pelos testes em `app/tests/test_finance.py`.

## Ferramentas

| Tool | O que faz |
|---|---|
| `analisar_compra` | Análise completa: custo em horas, % da renda, atraso na meta e veredito ("Vale a pena" / "Melhor esperar" / "Não compre agora") |
| `custo_em_horas` | Cálculo rápido: quantas horas de trabalho um valor custa |

Ambas são **read-only** e puras (sem efeitos colaterais).

## Como rodar

```bash
cd mcp_server
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate        # Linux/Mac
pip install -r requirements.txt
python server.py                 # inicia via stdio
```

## Plugar no Claude Desktop

Edite o `claude_desktop_config.json` (em *Settings → Developer → Edit Config*) e
adicione, ajustando o caminho absoluto:

```json
{
  "mcpServers": {
    "financescope": {
      "command": "python",
      "args": ["C:/Users/KABUM/Desktop/FinanScope/mcp_server/server.py"]
    }
  }
}
```

Reinicie o Claude Desktop. Depois é só perguntar em linguagem natural:

> "Ganho R$ 4.000 por mês, trabalho 160h e guardo R$ 500. Vale a pena um celular
> de R$ 3.000 em 10x?"

O Claude chama `analisar_compra(valor=3000, renda_mensal=4000, horas_mensais=160,
parcelas=10, aporte_meta=500)` e responde com o veredito.

## Testar sem cliente

```bash
python -c "import asyncio, server; \
print(asyncio.run(server.mcp.call_tool('custo_em_horas', {'valor':350,'renda_mensal':4000,'horas_mensais':160}))[0][0].text)"
```

## Avaliações

`evaluation.xml` traz perguntas determinísticas (com respostas verificáveis) que
exercitam as ferramentas — útil para checar que um cliente LLM as usa corretamente.

---

## 2) `financescope_consultor_mcp` — consultor sobre dados reais

Diferente do anterior, este consulta as **suas finanças reais** via a API read-only
do FinanceScope (`/api/*`), autenticada por **token pessoal**.

### Ferramentas

| Tool | O que faz |
|---|---|
| `resumo_financeiro` | Receitas, despesas e saldo de um mês |
| `gastos_por_categoria` | Despesas por categoria (com %) |
| `status_meta` | Progresso e prazo da meta principal |
| `posso_comprar` | RealCost **já com o seu perfil** (não precisa informar renda/horas) |

Todas **read-only**.

### Configuração

1. No app, vá em **Perfil → Token de API → Gerar token** e copie o token.
2. Garanta que o FinanceScope esteja no ar (local ou deploy).
3. No `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "financescope_consultor": {
      "command": "python",
      "args": ["C:/Users/KABUM/Desktop/FinanScope/mcp_server/consultor_server.py"],
      "env": {
        "FINANCESCOPE_API_URL": "http://127.0.0.1:5000",
        "FINANCESCOPE_API_TOKEN": "cole-seu-token-aqui"
      }
    }
  }
}
```

Depois pergunte naturalmente:

> "Quanto gastei com lazer esse mês? E quando atinjo minha reserva?"

O Claude chama `gastos_por_categoria` e `status_meta` e responde com **os seus dados**.

> 🔒 O token dá acesso **somente-leitura** às suas finanças. Trate como uma senha;
> revogue na página de Perfil quando quiser.
