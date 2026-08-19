# Final validation (`ehb26-research`)

Recorded after the full synthetic experiment pipeline (`config.name=full`, seed 67, 24 virtual subjects, 2592 windows).

## Git

- Experiment manifest SHA: see `research/results/manifest.json` (`git_sha` field).
- Branch: `ehb26-research` (do not overwrite `main`).

## Environment

From `research/results/manifest.json`:

- Python 3.13.2, macOS arm64
- numpy 2.4.6, scikit-learn 1.7.2, pydantic 2.11, FastAPI 0.128
- `xstep_ml` 0.4.0

Re-create with `bash scripts/setup_env.sh` (Python ≥ 3.10).

## Tests

```
source .venv/bin/activate
python -m ruff check xstep_ml tests research/experiments api scripts
python -m pytest tests -q
```

Last local run: **35 passed**, ruff clean on the checked paths.

## Models evaluated

Gait-pattern characterization (9 classes), **synthetic** GroupKFold-by-subject:

threshold heuristic, majority, logistic regression, decision tree, linear SVM, random forest, GBM, MLP, hist-GBM.

Zone GBM trained on **derived** simulator labels. Production artifacts rewritten by `research/experiments/run_research.py` with the current sklearn.

## Datasets

- `synthetic_gait_v1` / `data_source=synthetic` / `validation_type=engineering_simulation`
- Dataset hash in `research/results/manifest.json`
- No human walking data, no PHI
- Ulcer photograph archive **not** in this checkout (Table 7 placeholder)
- Calibration measurements: **simulated example only**

## Figures generated

Under `research/figures/` as PNG+PDF+SVG, including architecture, plantar layout, pipeline, simulated gait cycle, calibration demo (labeled simulated), confusion, model comparison, sensor ablation, robustness, latency, simulated longitudinal example, ulcer placeholder.

## Known limitations

See `/RESEARCH_LIMITATIONS.md`. BLE radio airtime and battery were not measured. Bootstrap N in this run was 80 (raise `BOOTSTRAP_N` for camera-ready CIs). MLP did not fully converge at `max_iter=80`.

## Outstanding requirements for real clinical validation

1. Ethics-approved human walking sessions (`research/protocols/REAL_DATA_PROTOCOL.md`) — **not** this file.
2. Physical FSR bench calibration filled into `data/calibration/TEMPLATE.csv`.
3. Independent site/overload labels (not derived from gait class).
4. Prospective outcome labels if ulcer-risk claims are ever attempted.
5. Instrumented BLE/airtime and battery logs.
6. Patient-level splits for any photograph model used in the same paper.

Until then, all gait/zone metrics remain **engineering/simulation validation**.
