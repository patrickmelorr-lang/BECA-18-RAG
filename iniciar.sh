#!/usr/bin/env bash
# Equivalente para macOS y Linux.  Uso:  ./iniciar.sh instalar | app | bot | costos
set -e
cd "$(dirname "$0")"

instalar() {
  [ -d .venv ] || python3 -m venv .venv
  source .venv/bin/activate
  pip install --upgrade pip
  pip install torch --index-url https://download.pytorch.org/whl/cpu
  pip install -r requirements.txt
  [ -f .env ] || { cp .env.example .env; echo "Edita .env con tus llaves y vuelve a correr."; exit 0; }
  python build_index.py
}

case "${1:-app}" in
  instalar) instalar ;;
  app)      source .venv/bin/activate && streamlit run app.py ;;
  bot)      source .venv/bin/activate && python bot.py ;;
  costos)   source .venv/bin/activate && python -m src.costs ;;
  *)        echo "Uso: ./iniciar.sh [instalar|app|bot|costos]" ;;
esac
