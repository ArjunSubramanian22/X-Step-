# Model card (gait / zone / optional ulcer CNN)

## Gait pattern model

- **Task:** 9-class biomechanical pattern characterization (not ulcer diagnosis).
- **Input:** 59 features from 8-channel windows (MET1/MET2/MET5/HEEL × left/right).
- **Architecture (production):** \(\ell_2\) logistic regression after StandardScaler (`gait_pipeline`). Artifact filename `gait_pattern_rf.joblib` is historical.
- **Data:** **Synthetic** virtual subjects unless replaced. Validation type: engineering/simulation.
- **Splits:** GroupKFold / grouped hold-out by subject. IID window splits are leakage and are tested against.
- **Metrics:** See `research/tables/table3_model_comparison.csv` (do not copy stale numbers into this card).

## Zone model

- Gradient boosting on the same features.
- Labels are **derived from the gait class** in the simulator (not an independent clinical annotation).

## Ulcer photograph CNN

- Public DFU images; optional; gitignored.
- Unpaired with insole streams. Interpretability (Grad-CAM) is not clinical validation.

## Efficiency

`research/tables/efficiency.csv` after `make experiments`.

## Out of scope

FDA clearance, amputation reduction, real-world diagnostic sensitivity/specificity, superiority to Moticon/Pedar/Tekscan.
