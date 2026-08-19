# Terminology

Canonical scientific terms for X-Step (EHB 2026). Use these in the manuscript, tables, figure captions, and model cards.

## Sensor sites (hardware)

| Canonical | Anatomy | Firmware / ML token | App UI alias (not a fifth site) |
| --- | --- | --- | --- |
| MET1 | first metatarsal head | `met1` | `toes` |
| MET2 | second metatarsal head | `met2` | `ball` |
| MET5 | fifth metatarsal head | `met5` | `arch` |
| HEEL | calcaneus / heel | `heel` | `heel` |

Do not write “ball of foot” for MET2 unless explicitly discussing the app alias. MET5 is the lateral column (fifth metatarsal), not the medial arch.

## Preferred phrases

| Use | Do not use as a synonym |
| --- | --- |
| plantar pressure | “foot force” without kPa/N |
| sensor site | “zone” except for derived zone labels |
| overload event | “ulcer event” |
| pressure-time integral (PTI) | “area under the curve” without units (kPa·s) |
| peak plantar pressure (PPP) | “max load” without kPa |
| gait feature | “AI embedding” |
| risk score | “diagnosis score” |
| engineering risk-alert threshold | “clinical cut-off”, “ulcer threshold” |
| real-time monitoring | “on-device MCU inference” unless measured |
| synthetic validation | “clinical validation” |
| subject-independent evaluation | “IID accuracy” as the headline |
| biomechanical risk monitoring | “ulcer detection” |
| decision-support / risk-alert framework | “autonomous treatment” |
| feasibility study | “proven medical device” |

## Evidence levels

- **Level A** — physical engineering (bench calibration, BLE on the air, power, human repeatability).
- **Level B** — algorithmic (grouped ML, ablation, simulated robustness).
- **Level C** — clinical outcomes (ulcers, amputations, clinician decisions).

Never report Level B as Level C.

## Model names

Production gait head: **logistic regression** (`logreg`). Artifact filename `gait_pattern_rf.joblib` is historical and must not be described as a random forest.
