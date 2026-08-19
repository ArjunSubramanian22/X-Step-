# EHB 2026 readiness report

**Date:** 2026-08-19  
**Branch:** `ehb26-research`  
**Be critical. Scores are not inflated.**

This is a **methods / engineering** package with a complete software freeze and **no human plantar dataset**. That caps several axes.

## Scores (0–100)

| Axis | Score | Rationale |
|------|------:|-----------|
| Novelty | 48 | Sparse FSR insoles exist (e.g. SmartStep). Novelty is the documented 4-site DFU-region contract + ablation/robustness/grouped ML, not a new sensing physics. |
| Methodological rigor | 78 | Grouped splits, leakage tests, frozen HPs, CIs, ablation, perturbations, generated Results. Labels are still synthetic. |
| Hardware validation | 28 | Firmware exists; assumed to work per project brief. No bench curve, no measured SNR, no in-shoe trace in git. |
| ML validation | 62 | Strong **simulator** protocol (subject/session/LOSO/IID). Zero external human test. Zone labels derived from gait class. |
| Statistics | 70 | Bootstrap CIs, SAP, error analysis. Frozen tables used n_boot=80. No clinical estimand. |
| Reproducibility | 82 | Lockfile, freeze doc, Makefile, CI smoke, importer, split dumps. Full 9-model CV is slow but specified. |
| Real-time implementation | 55 | Host latency measured; radio, jitter buffer, and MCU inference are not. 25 Hz spec is firmware delay. |
| Clinical claim discipline | 88 | Explicit non-claims; ulcer CNN out; LLM out; engineering thresholds. Residual risk is framing in the title (“diabetic foot care”). |
| Paper quality | 68 | Complete skeleton + generated Results + related-systems table. Needs real traces or it reads as a toolbox. |
| Reference quality | 84 | Core citations verified (Fernando year corrected; IWGDF authors corrected; Goyal removed from primary). |

## Overall readiness score

**58 / 100**

Fit for an EHB **methods** submission only after the program committee’s appetite for simulation-only wearables is accepted. **Not** fit as a clinical DFU or hardware-characterization paper without new measurements.

## Strongest contribution

A leakage-safe, fully specified four-site pipeline (protocol, features, grouped baselines, ablation, robustness curves) that answers a narrow engineering question without fabricating patients.

## Weakest component

**Physical and human evidence:** calibration, BLE, power, and walking all remain empty.

## Five likely reviewer objections

1. No human walking data / N=0.
2. Calibration error is simulated.
3. “Real-time wearable” without radio or battery.
4. Synthetic labels may be linearly separable (peak features ≈ full set).
5. Incremental vs existing FSR insoles; DFU framing overreaches.

## Five remaining highest-value actions

1. Load-cell calibration of all four sites (loading/unloading).
2. ≥10 participants, ≥2 sessions, grouped evaluation (ethics as required).
3. Phone-side BLE timestamps vs `t_ms` (airtime, loss).
4. Rail current per `POWER_MEASUREMENT_PROTOCOL.md`.
5. Rename `gait_pattern_rf.joblib` and drop DFU-prevention language from any leftover posters.

## Experiments still requiring physical data

- Sensor calibration MAE/RMSE on this hardware
- Hysteresis and drift of installed FSRs
- BLE packet loss and notify latency
- Battery / average power
- Representative **real** pressure figure

## Experiments still requiring human-subject data

- Within- and between-session repeatability (ICC)
- Subject-independent performance in people
- Session-independent performance in people
- Footwear/speed effects
- Any clinical endpoint (ulcer, offloading adherence)—separate, ethics-heavy study

## Claims currently safe to make

- We implemented a four-site 25 Hz BLE insole stack and a reproducible ML/feature pipeline.
- On a **virtual** 24-subject cohort, grouped logreg macro-F1 is high and some sensor dropouts hurt.
- Host logreg inference is computationally light vs 40 ms sampling.
- Robustness **simulations** show operating regions and failures.
- We do not have patient accuracy.

## Claims that must not be made

- Prevents ulcers or amputations
- Diagnoses DFU, infection, or ischemia
- Clinically validated / FDA / hospital trial
- Predicts ulcers
- Superior accuracy vs commercial insoles
- Human repeatability or battery hours
- That synthetic accuracy is clinical accuracy
- That StepMate is a scientific contribution or a risk engine
