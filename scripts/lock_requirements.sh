#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
source .venv/bin/activate 2>/dev/null || true
python -m pip freeze > requirements.lock
echo "Wrote requirements.lock ($(wc -l < requirements.lock) lines)"
