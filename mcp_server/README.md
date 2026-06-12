# financescope_mcp — RealCost via MCP

Servidor [MCP](https://modelcontextprotocol.io) que expõe o **RealCost Engine** do
FinanceScope como ferramentas para um assistente (ex.: Claude Desktop).

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
