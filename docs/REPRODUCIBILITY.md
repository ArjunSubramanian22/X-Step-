# Reproducibility

## Environment
Python 3.10+ is required. On macOS, `python3` may still be 3.7; do **not** pip-install this project with that interpreter.

```bash
bash scripts/setup_env.sh
source .venv/bin/activate
make test
make experiments
```

Deep-learning extras (ulcer/heatmap CNNs):

```bash
WITH_DL=1 bash scripts/setup_env.sh
```

## Seeds
Default seed `67` for cohort generation, models, and bootstrap.

## Paper artifacts
- Tables: `papers/ehb2026/tables/ehb_results.json`
- Figures: `papers/ehb2026/figures/*.png` (300 dpi) and `*.pdf` (vector)
- Blind text: `papers/ehb2026/manuscript_blind.md` (paste into the official EHB Springer Word template; 6–15 pages, USA English, no author block for review)

## What is not reproduced here
Gait-lab gold standard, Baylor Scott & White identifiable traces, and insurance-claim outcomes.
