# Ulcer photograph model — out of the primary EHB paper

## Decision

**Do not include the DFU image CNN as a core contribution of the four-site insole paper.**

Reasons:

1. Images are unpaired with X-Step FSR streams.
2. Provenance is a public Roboflow/Kaggle-style archive (ADPM V3.3, MIT), not a local consented DFU cohort tied to this device.
3. Patient-level identity is not available; leakage control is source-id grouping at best.
4. Adding a second, weakly validated clinical-vision story would make the submission two thin papers.
5. The primary research question is sparse plantar sensing + robustness + wearable deployment.

The insole paper must stand without this model.

## Where it may appear

- Supplementary note (this file + `table7_ulcer.csv` showing the default pipeline skipped training)
- Future work: paired photo + pressure only if ethics and identifiers exist
- Product/app (optional), never as the scientific novelty

## What must not be claimed

- That photograph grade predicts insole pressure
- That the CNN diagnoses infection or ischemia
- Any metric not produced by `scripts/train_ulcer.py` on a present archive with grouped splits
