# Data inventory

Date: 2026-08-19. Machine-readable twin: `research/data_inventory.json`.

This inventory exists so reviewers can see **what was actually measured** versus **what was simulated**. Synthetic traces are never described as human observations.

## Search performed

The repository was searched for raw FSR recordings, walking sessions, calibration trials, BLE logs, participant metadata, pressure traces, gait trials, and ulcer image archives.

**Finding:** there are **no in-repo human plantar-pressure recordings** and **no field BLE logs**. Calibration CSVs contain a **simulated** example plus an empty template.

## Datasets

### 1. Synthetic 4-FSR gait cohort — `synthetic_4fsr_gait`

| Field | Value |
|-------|--------|
| Source | `make_cohort_bundle` in `xstep_ml/data/synthetic_gait.py` |
| Real vs synthetic | **synthetic** |
| Subjects | 24 virtual |
| Sessions | 216 (`s{sid}_g{gait}` — one simulated gait condition per session) |
| Windows | 2592 (12 windows × 9 classes × 24 subjects) |
| Samples | 2592 × 100 time steps = 259 200 frames (not independent patients) |
| Strides | **not counted** (fixed 4 s windows, not stride segmentation) |
| Labels | 9 overload-pattern classes; zone labels **derived from** gait class |
| Rate / sensors | 25 Hz; MET1, MET2, MET5, HEEL (bilateral → 8 channels) |
| Missingness | optional simulated drops (`drop_prob` ≤ 0.04) |
| Purpose | grouped ML, ablation, robustness |
| Train/test | GroupKFold by virtual `subject_id` only |
| Publication | **engineering / in-silico** only |
| Consent | n/a |

This is the **only** dataset behind the frozen model-comparison, ablation, and robustness tables.

### 2. Simulated calibration curve — `calibration_simulated_example`

| Field | Value |
|-------|--------|
| Source | `simulate_example_curve` |
| Real vs synthetic | **synthetic** |
| n | 50 ADC/force pairs (loading + unloading) |
| Purpose | exercise MAE/RMSE/MAPE/hysteresis code |
| Publication | must be captioned **SIMULATED** — **not** this insole’s bench error |

Recorded demo residuals (not physical): MAE ≈ 1.30 N, RMSE ≈ 2.02 N, MAPE ≈ 4.7% (`research/results/calibration_simulated.json`).

### 3. Calibration template — empty

`data/calibration/TEMPLATE.csv` has no measurements. Do not fill it with invented loads.

### 4. Human walking / FSR / BLE — **absent**

| Field | Value |
|-------|--------|
| Path | `data/raw/` (drop-in target for `python -m research.import_real_data`) |
| Subjects / sessions / samples / strides | **0** |
| Eligibility | not train/test, not publication as human data |
| Consent | none on file |

Repeatability ICC, session generalization in patients, BLE airtime, and battery runtime **require these recordings**. Pipelines exist; values are not fabricated.

### 5. Ulcer photographs — `ulcer_adpm_v3_3_roboflow`

Public Roboflow ADPM V3.3 classification (MIT, per `ulcer model/archive/README.dataset.txt`). Image pixels are **gitignored**. They are **not** paired with X-Step FSR streams.

**Decision:** keep out of the **primary** EHB insole paper (supplementary / future work only). See `research/ULCER_MODEL.md` and `research/manuscript/SUPPLEMENTARY_ULCER.md`.

### 6. Heatmap RGB CNN — out of scope

Legacy Kaggle-style plantar heatmaps are a different modality. They do not justify four-site FSR claims.

## Rule

If a table or figure does not set `data_source` to `human` or `bench`, it is **not** a human or load-cell result.
