# EHB 2026 final acceptance-risk report

Critical scores after submission-hardening. Not a prediction of the actual PC.

| Axis | Score /10 | Note |
| --- | --- | --- |
| Novelty | 5 | Combinatorial (sparse contract + ablation + grouped ML + robustness + host timing). Not new physics. |
| Experimental rigor | 6 | Strong for a simulator study; weak as a wearable validation. |
| Biomedical relevance | 6 | DFU mechanics are relevant; no patients. |
| ML methodology | 7 | Grouped CV, IID contrast, a priori HPs, leakage tests. Task is easy-ish. |
| Hardware validation | 3 | Spec + unit tests; no bench/radio/power. |
| Robustness evaluation | 7 | Failure modes shown; perturbations simulated. |
| Reproducibility | 8 | Registry, tests, `make paper`, freeze. sklearn drift remains. |
| Writing quality | 7 | One thesis; Level A/B/C; captions. Template page count unknown. |
| Reference integrity | 8 | 12 verified DOIs; no invented refs. |
| Claim discipline | 8 | Conservative; CITATION.cff prevention language removed. |

**Overall readiness: 65/100**

Previous readiness (~58) rose mainly from claim/registry/methods/reproducibility work, **not** from new physical data.

## Top 5 acceptance arguments

1. Honest, complete methods for a sparse four-site insole with a documented BLE contract.
2. Ablation with CIs: MET5/HEEL matter; MET1 does not (on this generator).
3. IID vs grouped split as a leakage lesson other wearable ML papers skip.
4. Robustness shows failure, not only success.
5. Host latency and model size support a real-time **host** path without fantasy battery numbers.

## Top 5 rejection arguments

1. \(N=0\) X-Step four-site FSR walking sessions (32-cell walking is a different device).
2. Calibration and packet loss are not physical.
3. High AUROC is simulator peak-separability.
4. “Wearable deployment” still lacks radio and energy.
5. Novelty is incremental relative to SmartStep-class insoles and pressure reviews.

## Fatal flaws

None that are scientific fraud. The **submission-fatal** risk is presenting this as clinical validation. The text now forbids that. A remaining process risk: official Springer PDF not compiled in this environment.

## Experiments that would most improve the paper

1. Load-cell calibration of the four FSRs on the ESP32 ADC.
2. Over-the-air BLE notify timing and loss.
3. Ethics-approved walking (even healthy volunteers) with grouped evaluation.
4. Current draw at 25 Hz notify.

## Changes no longer worth doing before submission

- Retraining to beat 0.885 by 0.01.
- Putting the ulcer CNN back in the core paper.
- UI/chatbot screenshots as scientific figures.
- Ranking hist-GBM vs logreg.
- Inventing battery life from a datasheet.
