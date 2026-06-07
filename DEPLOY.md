# Deploy gratuito no PythonAnywhere

Guia para hospedar o FinanceScope de graça e acessar de qualquer lugar
(inclusive pelo celular), numa URL `https://SEU_USUARIO.pythonanywhere.com`.

O PythonAnywhere foi escolhido porque o banco **SQLite persiste** (contas e
dados dos usuários não se perdem) e o site fica **sempre online** — ideal para
um app com login.

---

## 1. Criar a conta

1. Acesse https://www.pythonanywhere.com e crie uma conta **Beginner (grátis)**.
2. Anote seu usuário — ele vira parte da URL (`SEU_USUARIO.pythonanywhere.com`).

## 2. Clonar o projeto

Na aba **Consoles → Bash**, rode:

```bash
git clone https://github.com/BrunoCarreiroCS/FinanScope.git
```

## 3. Criar o ambiente virtual e instalar dependências

```bash
mkvirtualenv --python=/usr/bin/python3.11 financescope
pip install -r ~/FinanScope/app/requirements.txt
```

> O ambiente `financescope` fica em `/home/SEU_USUARIO/.virtualenvs/financescope`.

## 4. Criar o banco de dados

```bash
cd ~/FinanScope/app
flask init-db        # cria as tabelas + categorias padrão
flask seed-demo      # opcional: cria o usuário demo com dados de exemplo
```

> Conta demo: `demo@financescope.app` / `demo1234`

## 5. Configurar o web app

Na aba **Web → Add a new web app**:

1. Escolha **Manual configuration** (NÃO o assistente "Flask").
2. Selecione **Python 3.11**.
3. Em **Virtualenv**, informe:
   `/home/SEU_USUARIO/.virtualenvs/financescope`
4. Em **Source code** / **Working directory**, informe:
   `/home/SEU_USUARIO/FinanScope/app`

## 6. Editar o arquivo WSGI

Clique no link do **WSGI configuration file** (algo como
`/var/www/SEU_USUARIO_pythonanywhere_com_wsgi.py`), **apague tudo** e cole o
conteúdo de [`app/wsgi_pythonanywhere.py`](app/wsgi_pythonanywhere.py),
trocando:

- `USERNAME` → seu usuário do PythonAnywhere
- `COLE_UMA_CHAVE_ALEATORIA_AQUI` → uma chave forte

Gere a chave no Bash:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## 7. Publicar

Volte na aba **Web** e clique em **Reload**. Pronto:

👉 **https://SEU_USUARIO.pythonanywhere.com**

Acesse pelo celular, crie sua conta e use normalmente. 🎉

---

## Atualizar o site depois (novos commits)

No Bash:

```bash
cd ~/FinanScope && git pull
```

Depois clique em **Reload** na aba Web.

> Se algum dia o **schema** do banco mudar, rode `flask init-db` de novo —
> atenção: isso **recria as tabelas e apaga os dados**.

## Observações

- O plano grátis dá **1 web app** e a URL `*.pythonanywhere.com` com HTTPS.
- Fontes e Chart.js são carregados via CDN **pelo navegador**, então funcionam
  sem precisar liberar acesso externo no servidor.
- Faça backup do banco copiando `app/instance/financescope.sqlite` quando quiser.
