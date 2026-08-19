#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

pick_python() {
  for c in python3.13 python3.12 python3.11 python3; do
    if command -v "$c" >/dev/null 2>&1; then
      ver="$("$c" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
      major="${ver%%.*}"
      minor="${ver#*.}"
      if [ "$major" -gt 3 ] || { [ "$major" -eq 3 ] && [ "$minor" -ge 10 ]; }; then
        echo "$c"
        return 0
      fi
    fi
  done
  echo "Need Python 3.10+. The default python3 on this machine is too old for current PyTorch/sklearn." >&2
  exit 1
}

PY="$(pick_python)"
echo "Using $($PY -V)"
if [ ! -d .venv ]; then
  "$PY" -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install -U pip setuptools wheel
python -m pip install -r requirements.txt
if [ "${WITH_DL:-0}" = "1" ]; then
  python -m pip install -r requirements-dl.txt
fi
python -m pip install -e .
echo "Activate with: source .venv/bin/activate"
