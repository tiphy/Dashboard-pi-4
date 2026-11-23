#!/bin/bash
# Mac: duplo clique | Linux: ./iniciar.command
cd "$(dirname "$0")"
PY=$(command -v python3 || command -v python)
[ -z "$PY" ] && { echo "Python nao encontrado. Instale em https://www.python.org/downloads/"; read -p "Enter para sair"; exit 1; }
[ -d .venv ] || $PY -m venv .venv
source .venv/bin/activate
if [ ! -f .venv/.instalado ]; then
  pip install --upgrade pip && pip install -r requirements.txt && touch .venv/.instalado || { read -p "Erro. Enter para sair"; exit 1; }
fi
mkdir -p ~/.streamlit
[ -f ~/.streamlit/credentials.toml ] || printf '[general]\nemail = ""\n' > ~/.streamlit/credentials.toml
[ -f dados/dados.json ] || python gerar_dados_exemplo.py
python -m streamlit run app.py
