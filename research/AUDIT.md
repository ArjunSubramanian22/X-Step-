# X-Step research audit (`ehb26-research`)

Audit date: 2026-08-19. Branch parent: `production-ml` @ `ab31d8c`.

This document records **what exists**, **what is synthetic**, and **which claims are publication-safe**. Hardware function (FSR capture + BLE stream) is assumed. Clinical outcomes are **not**.

## 1. Folder structure (current)

```
api/                 FastAPI inference
artifacts/           joblib gait/zone models + JSON reports
docs/                ethics, dataset/model cards
firmware/            ESP32 Arduino sketch
heatmap model/       legacy CNN notebooks + weights
mobile/              Expo 52 app
papers/ehb2026/      draft manuscript + 300 dpi figures
scripts/             train/eval/demo
tests/               6 pytest files (production + cohort)
tools/               OCR metric scraping (not scientific)
ulcer model/         CNN + Roboflow archive (images gitignored)
xstep_ml/            library: hardware, protocol, features, models, inference
```

Missing vs EHB-grade layout: `research/` experiment registry, canonical schema, calibration residuals, CI, lockfile, leakage tests, system latency table, auto-ingested manuscript metrics.

## 2. ML models

| Model | Task | Data | Artifact |
| --- | --- | --- | --- |
| Logistic regression pipeline (`gait_pipeline`) | 9-class gait overload pattern | **Synthetic** 4-FSR windows | `artifacts/gait_pattern_rf.joblib` (name stale) |
| Gradient boosting (`zone_pipeline`) | 5-class high-risk site | **Synthetic** (label derived from gait class) | `artifacts/high_risk_zone_gbm.joblib` |
| `UlcerNN` / ResNet-50 / EfficientNet-B0 | 4-class DFU photograph grade | Public Roboflow/Kaggle images | `ulcer model/ulcer_model_state.pth` |
| `HeatCNN` / transfer backbones | 9-class plantar heatmap RGB | Kaggle pickle (not insole FSR) | `heatmap model/heatmap_model_state.pth` |
| `MultimodalFusionModel` | Concat heatmap + ulcer embeddings | **No paired labels** | architecture only |
| Clinical linear score | IWGDF-style 0–3 prior | Rules, not learned | `xstep_ml/models/clinical.py` |
| Fusion health index | Weighted sum 0–100 | Specified weights | `xstep_ml/inference/engine.py` |
| On-device TS gait heuristics | Same 9 classes | Rules on peaks | `mobile/services/gaitEngine.ts` |

## 3. Datasets

| Dataset | Provenance | In repo? | Leakage risk |
| --- | --- | --- | --- |
| `make_cohort` 4-FSR windows | Simulated gait + subject mismatch | generated | GroupKFold by synthetic subject **if** `run_ehb_experiments.py` is used; `train_production.py` still uses IID stratified split |
| ADPM / Roboflow DFU photos | Public classification set | train/valid/test gitignored | Roboflow augment siblings historically leaked; `xstep_ml/data/splits.py` groups by source id |
| Pressure heatmap RGB pickle | Kaggle `mahdiislam/pressure-sensor-heatmaprgb` | downloaded at runtime | Random 80/20; **not** the 4-FSR insole |
| Physical FSR calibration | **None** | — | — |
| Prospective plantar + outcome | **None** | — | — |

## 4. BLE packet (28 bytes, little-endian)

`magic "XS" | version u8 | flags u8 | seq u16 | t_ms u32 | 4×u16 ADC | battery u8 | reserved u8 | 4×i16 temp tenths`

Channel order: MET1, MET2, MET5, HEEL. Flags: bit0 left, bit1 right, bit2 temp present, bit3 charging.

Firmware: `firmware/xstep_insole/xstep_insole.ino`, 25 Hz, Nordic UART-style UUIDs.

## 5. Metrics currently reported

- Production smoke: sklearn `classification_report` on **IID** holdout (inflates vs grouped CV).
- Paper script: accuracy, macro-F1, bootstrap 95% CI, McNemar, permutation importance, noise sweep, feature-group ablation.
- **Missing for EHB:** balanced accuracy, specificity, PR-AUC, Brier, reliability diagrams, sensor-count ablation, packet-loss/drift/jitter, window-size/fs sweeps, threshold ROC, latency P95, model size.

## 6. Split methodology

| Script | Split | Safe? |
| --- | --- | --- |
| `scripts/run_ehb_experiments.py` | 5-fold GroupKFold by virtual subject | Yes for synthetic subjects |
| `scripts/train_production.py` | `train_test_split(..., stratify=y)` **IID windows** | **No** — correlated windows from one subject can leak |
| Ulcer notebooks (legacy) | Random 80/20 on ImageFolder | **No** unless using `splits.py` |
| Heatmap notebooks | sklearn 80/20 | Weak (no subject metadata) |

## 7. Duplication / stale names

- Gait artifact still named `gait_pattern_rf.joblib` while production classifier is logistic regression.
- Feature extraction duplicated in Python (`biomechanics.py`) and TypeScript (`gaitEngine.ts`) with incomplete feature parity.
- Ulcer architecture defined in `ulcer_model.py`, `xstep_ml/models/ulcer.py`, and notebooks.
- `papers/ehb2026` vs requested `research/` dual homes.

## 8. Dependencies

- Python: 3.10+ required; default macOS `python3` may be 3.7.
- Core unpinned loosely via `>=`; no `requirements.lock`.
- Torch optional (`requirements-dl.txt`).
- Expo 52; BLE via optional `react-native-ble-plx` dynamic import (not in `package.json`).
- No GitHub Actions CI.

## 9. Tests (current)

`tests/test_production.py` (protocol, features, engine), `tests/test_cohort.py` (subject ids). **No** leakage assertion, calibration, API client, malformed packets, missing-channel, reproducibility hash tests.

## 10. Claim–evidence table

| Claim | Current Evidence | Evidence Type | Strength | Publication Safe? | Required Validation |
| --- | --- | --- | --- | --- | --- |
| Four FSRs at MET1/MET2/MET5/HEEL stream via BLE | Firmware + protocol + assumed hardware | Engineering | Medium | Yes, as **system description** | Bench capture logs |
| 25 Hz in-shoe monitoring is feasible | Firmware delay + protocol | Engineering | Medium | Yes as **design choice** | Measured Hz, packet loss, battery |
| Features PPP/PTI/asymmetry/cadence computed from 8-ch windows | `biomechanics.py` + unit tests | Software | High | Yes | Golden-vector tests |
| 9-class gait pattern discrimination | GroupKFold on **synthetic** cohort | **Synthetic validation** | Medium for simulator; **none** for patients | Yes **only** if labeled synthetic | Human walking with labels |
| Zone localization head | Zone = deterministic map of gait class | **Synthetic validation** | Weak (not independent task) | Disclose as derived label | Independent site annotation |
| Logistic regression > RF on this feature set | McNemar on synthetic OOF | **Synthetic validation** | Medium in silico | Yes with grouping + CI | Confirm on real traces |
| Health index 0–100 | Weighted sum of clinical rules + peaks | Heuristic | Low as clinical score | Yes as **engineering index** | Outcome-labeled cohort |
| Ulcer photo 4-class CNN | Public images; leakage historically possible | Public computer vision | Medium if grouped splits | Yes as **photo grading**, not insole | Patient-level split |
| Multimodal fusion improves care | Architecture only; unpaired data | None | None | **No performance claim** | Paired pressure+photo labels |
| Prevents ulcers / amputations | None | None | None | **No** | Prospective clinical trial |
| FDA / diagnostic device | Explicitly not | None | — | Must remain **no** | Regulatory pathway |
| Superior to Moticon/Tekscan accuracy | None | Marketing (removed from research framing) | None | **No** | Head-to-head lab study |
| Thermal 2.2 °C rule | Literature, reserved packet fields | Citation, not measured here | — | Cite literature only | On-device thermistors |
| Alert threshold 75 kPa | Engineering default | Arbitrary | Low | Call **engineering alert threshold** | Threshold sweep + clinic |

## 11. Undocumented assumptions

- Linear ADC→kPa (`KPA_FULL_SCALE=250`) without FSR Steinhart/log force curve.
- Left/right packets independently timestamped; fusion assumes clocks are close.
- Synthetic overload classes equal clinical “risk.”
- 200 kPa “high-risk” band from plantar-pressure literature, not this device’s calibration.

## 12. Implications for EHB 2026

Safe paper: **wearable architecture + feature pipeline + synthetic/engineering validation + robustness + latency**. Unsafe paper: **clinical DFU prediction, prevention rates, device superiority.**
