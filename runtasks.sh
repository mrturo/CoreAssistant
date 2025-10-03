#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${GREEN}CoreAssistant Task Runner${NC}"

cd "$(dirname "$0")"

if [[ -x ".venv/bin/python" ]]; then
  PYBIN=".venv/bin/python"
else
  if command -v python3 >/dev/null 2>&1; then PYBIN="python3"
  elif command -v python >/dev/null 2>&1; then PYBIN="python"
  else
    echo "No Python found. Install Python 3 or create .venv"; exit 1
  fi
fi

if [[ -x ".venv/bin/streamlit" ]]; then
  STREAMLIT=".venv/bin/streamlit"
else
  STREAMLIT="streamlit"
fi

export PYTHONPATH="${PYTHONPATH:-}:."

maybe_caffeinate() {
  if [[ "$(uname -s)" == "Darwin" ]] && command -v caffeinate >/dev/null 2>&1; then
    caffeinate -dimsu &
    CAFFE_PID=$!
    trap '[[ -n "${CAFFE_PID:-}" ]] && kill -TERM "$CAFFE_PID" 2>/dev/null || true' EXIT INT TERM
  fi
}

unset_proxies() {
  unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY || true
}

runm() { "${PYBIN}" -m "$@"; }
runp() { "${PYBIN}" "$@"; }

CMD="${1:-pending}"

case "${CMD}" in
  planned_item)
    echo -e "${GREEN}Listing pending tasks and upcoming events...${NC}"
    unset_proxies
    maybe_caffeinate
    runm src.planned_item.main_with_todoist
    ;;

  *)
    echo "Usage: bash runtasks.sh {planned_item|all}"
    exit 2
    ;;
esac
