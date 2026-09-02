# Data inventory

Date: 2026-08-19. Machine-readable twin: `research/data_inventory.json`.

This inventory exists so reviewers can see **what was actually measured** versus **what was simulated**. Synthetic traces are never described as human observations.

## Search performed

The repository was searched for raw FSR recordings, walking sessions, calibration trials, BLE logs, participant metadata, pressure traces, gait trials, and ulcer image archives.

**Finding:** there are **no in-repo X-Step four-site FSR walking recordings**. There **is** an operator-provided 32-cell insole + OptiTrack walking archive (15 adults, 149 analyzed takes). Calibration CSVs contain a simulated example, an empty template, and operator-attested four-site bench data.

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

### 4. Human walking / X-Step 4-FSR — **absent**

| Field | Value |
|-------|--------|
| Path | `data/raw/` (drop-in target for `python -m research.import_real_data`) |
| Subjects / sessions / samples / strides | **0** |
| Eligibility | not train/test as X-Step FSR walking |
| Consent | none on file |

### 4c. Human walking / 32-cell insole + OptiTrack — `human_32site_insole_optitrack`

| Field | Value |
|-------|--------|
| Source | Operator zip `InsolesOpitrackDataset.zip` (layout matches Zenodo 10.5281/zenodo.20156243) |
| Hardware | 32 pressure channels/foot + IMU + CoP + OptiTrack Baseline Lower; **not** X-Step FSR402 |
| Subjects | 15 (7 female, 8 male; age 19–30, mean 23.4) |
| Takes | 150 unique pressure takes; 149 analyzed (P13 M1 excluded) |
| Rate | no timestamps; 64 Hz assumed |
| Purpose | sparse four-site vs dense regional load / AP CoP |
| Publication | human walking on a **different** insole; do not mix into frozen synthetic F1 |

SHA-256 of the zip: `6f11afbb50c555738ead3be7051218c1e79ecd29ed8ac53e404e8f770133561a`. Evaluator: `python -m research.experiments.evaluate_insoles_optitrack`.

### 4b. Four-site FSR force–ADC bench — `four_site_fsr_bench`

| Field | Value |
|-------|--------|
| Path | `data/calibration/four_site_fsr_bench.csv` |
| Original upload name | `Real_data.csv` |
| Real vs synthetic | **bench (operator-attested)** |
| Provenance | Experimenter states the pairs were measured; LLM cleanup stamps archived |
| Sites / trials / rows | 4 sites × 5 trials × 12 loads × loading/unloading = 480 |
| Purpose | ADC→force reconstruction and hysteresis |
| Publication | Level A operator-attested calibration; **not** walking |

Repeatability ICC on X-Step four-site walking, session generalization in patients, BLE airtime, and battery runtime **remain unmeasured on the FSR402 prototype**. The 32-cell archive is a different device.

### 5. Ulcer photographs — `ulcer_adpm_v3_3_roboflow`

Public Roboflow ADPM V3.3 classification (MIT, per `ulcer model/archive/README.dataset.txt`). Image pixels are **gitignored**. They are **not** paired with X-Step FSR streams.

**Decision:** keep out of the **primary** EHB insole paper (supplementary / future work only). See `research/ULCER_MODEL.md` and `research/manuscript/SUPPLEMENTARY_ULCER.md`.

### 6. Heatmap RGB CNN — out of scope

Legacy Kaggle-style plantar heatmaps are a different modality. They do not justify four-site FSR claims.

## Rule

If a table or figure does not set `data_source` to `human` or `bench`, it is **not** a human walking or bench result. `bench` here means operator-attested FSR load–unload unless a lab notebook is also on file.
