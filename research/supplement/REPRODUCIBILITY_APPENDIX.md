# Reproducibility appendix

This appendix does **not** retrain models. Publication numbers are frozen in CSV/JSON.

## Environment (from `research/results/manifest.json`)

- Python 3.13.2 on the freeze machine (CI tests 3.11/3.12; project requires ≥3.10)
- Packages recorded in the manifest (`numpy`, `sklearn` 1.7.2, `matplotlib`, …)
- `xstep_ml` 0.4.0
- Random seed **67**
- Dataset hash `26180f5e5330adeac3088c43353bb05e83d90a120e2703ac673ec65e2781cd92`
- Experiment git SHA recorded in the manifest at table generation: `8baadaf6b27b527c44e050e9bcb80828c1632d67` (historical; current HEAD is recorded in `final_results_registry.json` at paper build)

## Hardware/software for latency

Host CPU timings in `latency_host.json` are machine-specific. Firmware sample period 40 ms is a **specification**, not a scope trace.

## Commands

```bash
bash scripts/setup_env.sh
source .venv/bin/activate
make test
make paper          # registry, rounded tables, figures, lint, dist/ehb26; does not train
```

Training (separate, do not run to chase decimals):

```bash
make experiments    # research/experiments/run_research.py
make final-eval     # writes smoke/ unless configured otherwise
```

Human import (no files in this checkout):

```bash
python -m research.import_real_data
```

## Model artifacts

Production gait head is logistic regression. File `artifacts/gait_pattern_rf.joblib` is a historical name. Hash locally after freeze; do not commit private health data.

## Regenerating figures/tables without retraining

```bash
python research/experiments/build_registry.py
python research/experiments/generate_results.py
python research/experiments/generate_figures.py
python -m research.build_paper --skip-figures
```
