# Reproducibility

## Environment

Python **3.10–3.13** (`.python-version` recommends 3.11). macOS `python3` may still be 3.7 — use `scripts/setup_env.sh`.

```bash
make setup
source .venv/bin/activate
make test
RESEARCH_SMOKE=1 python research/experiments/run_research.py   # CI-like
make paper-assets                                             # full regen
bash scripts/lock_requirements.sh                             # writes requirements.lock
```

Deep learning extras (ulcer/heatmap): `WITH_DL=1 bash scripts/setup_env.sh`.

## One-command paper assets

`make paper-assets` regenerates models where the synthetic trainer runs, metrics JSON/CSV, figures (PNG/PDF/SVG), tables, and `research/manuscript/results_fragment.md`.

## Recorded metadata

Each run writes `research/results/manifest.json` with git SHA, Python version, OS, package versions, dataset hash, and config. Seeds default to **67**.

## What a reviewer can reproduce

Non-clinical, synthetic gait/zone experiments, calibration **pipeline demo**, host latency of decode/features/sklearn, unit tests, API tests.

## What is not reproduced here

Gait-lab gold standard, identifiable clinical traces, BLE radio airtime, battery life, prospective ulcer outcomes, FDA studies.
