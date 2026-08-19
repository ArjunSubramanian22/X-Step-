# EHB 2026 experimental freeze

This file identifies **exactly** which code and configurations generate the paper results.

Do not treat later exploratory notebooks as part of the freeze unless they are listed here.

## Git

| Item | Value |
|------|--------|
| Branch | `ehb26-research` |
| Infrastructure freeze SHA | `097a1a8cf60298b47a6f7e3cb170d07eeb27eabd` (`record final validation and CI mobile checks`) |
| Intended tag | `v0.9-ehb26-experimental` |
| Tag status | Applied after last-mile tests: see `tagged_sha` in `freeze_config.json` |
| Package version | `xstep_ml` 0.4.0 |

The last-mile importer, split dumps, extra robustness sweeps, and generated Results live in commits **after** the infrastructure SHA. Re-record the tagged SHA in `freeze_config.json` (`tag_applied: true`) when the tag is created.

Machine-readable copy: `research/releases/freeze_config.json`.

## Hardware and firmware (assumed functional; not re-measured in software)

| Item | Frozen value | Source |
|------|----------------|--------|
| Hardware revision | `esp32-dev-fsr402-4ch` | `xstep_ml.hardware.HARDWARE_REVISION` |
| Firmware version | `insole-protocol-v1` | `xstep_ml.hardware.FIRMWARE_VERSION` |
| MCU | ESP32 Dev Module | `firmware/README.md` |
| Sensors | 4 × FSR402-class | firmware + hardware contract |
| Sites (canonical) | MET1, MET2, MET5, HEEL | GPIO 34 / 35 / 32 / 33 |
| Circuit | High-side FSR, 10 kΩ to ground, 3.3 V | firmware |
| ADC | 12-bit, full scale 4095 | `ADC_FULL_SCALE` |
| Sampling frequency | **25 Hz** (`delay(1000/SAMPLE_HZ)`) | `firmware/xstep_insole/xstep_insole.ino` |
| BLE packet version | protocol **v1**, magic `XS`, **28-byte** little-endian | `xstep_ml/protocol.py` |
| GATT | Nordic UART-style UUIDs | `xstep_ml.hardware` |
| Device names | `XSTEP-L` / `XSTEP-R` | firmware |

Two insoles stream independently. The host concatenates left then right into an `(T, 8)` frame.

## Preprocessing and features

| Item | Frozen value |
|------|----------------|
| Preprocessing / engineering pressure map | `linear_adc_engineering_v0` — \(P_{\mathrm{kPa}} = (\mathrm{ADC}/4095)\times 250\) after unloaded baseline |
| Research calibration module | `xstep_ml.calibration` (log–log optional; **no physical bench curve in-repo**) |
| Feature extractor | `xstep_ml.biomechanics.extract_features` (`FEATURE_EXTRACTOR_VERSION = biomechanics-v59`) |
| Feature count | **59** (`FEATURE_NAMES`) |
| Window used in frozen cohort | **4.0 s** at 25 Hz (**100 samples**) |
| Alert threshold type | **engineering risk-alert operating point** (`ALERT_PRESSURE_KPA = 75`) |

The linear ADC→kPa map is **not** a fitted load-cell calibration. Sensor calibration error and ML accuracy are reported separately.

## Models

A priori hyperparameters (no test-set search): `research/configs/HYPERPARAMETERS.md` and `xstep_ml.evaluation.baselines.baseline_models`.

| Role | Model | Notes |
|------|--------|--------|
| Primary gait / overload-pattern head | Logistic regression (`class_weight=balanced`, `max_iter=400`) | Production artifact still named `gait_pattern_rf.joblib` |
| Zone head | Gradient boosting | Labels **derived from gait class** in the simulator |
| Baselines | threshold heuristic, majority, logreg, decision tree, linear SVM, random forest, GBM, MLP, hist-GBM | Same GroupKFold splits |
| LLM / StepMate | **Not a model in this freeze** | Interpretation layer only (`research/STEPMATE_SAFETY.md`) |

Random seed for estimators and the synthetic cohort: **67**.

## Synthetic cohort used for published tables

| Item | Value |
|------|--------|
| Generator | `xstep_ml.data.synthetic_gait.make_cohort_bundle` |
| `data_source` | `synthetic` |
| `validation_type` | `engineering_simulation` |
| Subjects (virtual) | 24 |
| Windows per class | 12 |
| Gait classes | 9 |
| Windows | 2592 |
| Dataset hash (frozen run) | `26180f5e5330adeac3088c43353bb05e83d90a120e2703ac673ec65e2781cd92` |
| Grouping | `subject_id` (GroupKFold, 5 folds) |
| Session IDs | `s{sid}_g{gait_index}` (one simulated gait condition per session) |

**No human plantar recordings are in this freeze.** Results must not be described as patient performance.

## Software environment (recorded with the frozen tables)

From `research/results/manifest.json` (experiment SHA at table generation: `8baadaf`):

| Item | Value |
|------|--------|
| Python | 3.13.2 |
| Platform | macOS arm64 (see manifest) |
| numpy | 2.4.6 |
| scipy | 1.16.3 |
| pandas | 2.3.3 |
| scikit-learn | 1.7.2 |
| matplotlib | 3.10.9 |
| joblib | 1.5.3 |
| pydantic | 2.11.10 |
| Dependency lock | `requirements.lock` |
| Requires | Python ≥ 3.10 (`pyproject.toml`) |

Reproduce with `make setup` then `source .venv/bin/activate`.

Published bootstrap CIs in `table3`/`table4` used **`n_boot = 80`** (manifest). The SAP still prefers 400; last-mile scripts may recompute CIs with 400 on stored or re-derived OOF predictions. Point estimates of accuracy/F1 are not bootstrap means except where a table column is explicitly the bootstrap mean.

## Commands that generate paper artifacts

```text
make setup
make test
make experiments          # research/experiments/run_research.py
make final-eval           # last-mile splits, packet-loss sweep, repeatability, calibration plots
make figures
make tables
make generated-results    # research/manuscript/generated_results.md
```

Or `make paper-assets` (runs the chain).

CI smoke uses `RESEARCH_SMOKE=1` (tiny cohort) and **must not** overwrite the frozen full tables in a publication checkout without an explicit re-run.

## What is frozen vs not measured

**Frozen (software):** protocol, sites, 25 Hz spec, feature names, seeds, grouped-split code, baseline hyperparameters, synthetic generator.

**Not in this freeze as physical measurements:** BLE airtime, battery/runtime, load-cell calibration residuals, human walking traces, packet-loss from field logs.

If those measurements are added later, bump the freeze (new SHA, new dataset hash, new tag).
