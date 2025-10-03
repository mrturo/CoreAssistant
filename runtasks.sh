#!/usr/bin/env bash
# Fail fast + strict mode
set -euo pipefail

# ---------- Colors ----------
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}CoreAssistant Task Runner${NC}"

# ---------- Resolve project root & venv ----------
cd "$(dirname "$0")"

# Pick Python/Streamlit from venv if present, else from PATH
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

# Ensure 'src' package dir is discoverable for imports like '-m src.planned_item...'
# We need the PROJECT ROOT in PYTHONPATH, not './src'.
export PYTHONPATH="${PYTHONPATH:-}:."

# ---------- Helpers ----------
maybe_caffeinate() {
  # Only on macOS and if caffeinate exists
  if [[ "$(uname -s)" == "Darwin" ]] && command -v caffeinate >/dev/null 2>&1; then
    caffeinate -dimsu &
    CAFFE_PID=$!
    # Stop caffeinate on exit/signals
    trap '[[ -n "${CAFFE_PID:-}" ]] && kill -TERM "$CAFFE_PID" 2>/dev/null || true' EXIT INT TERM
  fi
}

unset_proxies() {
  unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY || true
}

runm() { "${PYBIN}" -m "$@"; }   # run python module
runp() { "${PYBIN}" "$@"; }      # run python file

# ---------- Commands ----------
CMD="${1:-pending}"

case "${CMD}" in
  pending)
    echo -e "${GREEN}Listing pending tasks and upcoming events...${NC}"
    unset_proxies
    maybe_caffeinate
    runm src.planned_item.list_pending_tasks
    ;;

  all)
    echo -e "${GREEN}Running full pipeline...${NC}"
    unset_proxies
    maybe_caffeinate
    runm src.planned_item.list_pending_tasks
    ;;

  *)
    echo "Usage: bash runtasks.sh {pending|all}"
    exit 2
    ;;
esac
