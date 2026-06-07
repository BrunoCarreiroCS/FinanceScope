# Template do arquivo WSGI do PythonAnywhere.
#
# NAO edite este arquivo no servidor: copie o conteudo abaixo para o
# "WSGI configuration file" que o PythonAnywhere cria na aba "Web",
# trocando USERNAME pelo seu usuario e a SECRET_KEY por uma chave aleatoria.
#
# Gere uma chave forte com:
#   python -c "import secrets; print(secrets.token_hex(32))"

import os
import sys

# Caminho da pasta 'app' do projeto (onde fica o app.py).
path = "/home/USERNAME/FinanScope/app"
if path not in sys.path:
    sys.path.insert(0, path)

# Variaveis de ambiente de producao.
os.environ["SECRET_KEY"] = "COLE_UMA_CHAVE_ALEATORIA_AQUI"
os.environ["SESSION_COOKIE_SECURE"] = "1"  # cookies so via HTTPS

# O PythonAnywhere procura por uma variavel chamada 'application'.
from app import app as application  # noqa: E402,F401
