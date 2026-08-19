# Statistical analysis plan (SAP)

Written **before** treating experiment outputs as camera-ready claims. This SAP applies to **engineering/simulation** labels unless a human dataset with a pre-registered endpoint is added.

## Estimands

1. **Primary (gait pattern):** macro-F1 of 9-class overload-pattern classification under 5-fold GroupKFold by subject ID, with percentile bootstrap 95% CI on pooled out-of-fold predictions.
2. **Secondary:** balanced accuracy, per-class recall/precision/F1/specificity, weighted-F1, confusion matrix. AUROC / PR-AUC / Brier / ECE only when class-aligned probabilities exist.
3. **Ablation estimands:** same primary metric after masking sensor subsets or feature groups.
4. **Robustness:** macro-F1 vs perturbation severity on a subject-held-out test set (model trained on unperturbed features).
5. **Threshold sweep:** sensitivity, specificity, false-alert rate, missed-event rate for an **engineering** binary (synthetic class ≠ `normal`). Not ulcer incidence.
6. **Latency:** host-side mean/median/P95 of decode, features, and inference. BLE airtime is out of scope until measured.

## Splits

- Default: GroupKFold by `subject_id`.
- Also report: GroupKFold by `session_id`, leave-one-subject-out, and IID StratifiedKFold as an **optimistic control** (may leak subjects).
- Artifact training: GroupShuffleSplit by subject (no window IID split).
- Split definitions are written to `research/results/splits/`.
- Tests **fail** if subject/session IDs overlap train/test (except the explicit IID control).

## Comparisons

- Pairwise model comparison: continuity-corrected McNemar on paired OOF correctness (exploratory on synthetic labels).
- Multiple model leaderboard: report CIs; if p-values are shown, Bonferroni-adjust \(\alpha/m\) and treat them as secondary.
- Effect size: Cohen's \(h\) on accuracy (optional).

## Missing data / perturbations

Packet drops and missing channels are **simulated**. They are not estimated from field logs in this repository.

## What we will not claim

- Statistical significance of clinical benefit.
- Diagnostic sensitivity/specificity for ulcers.
- Superiority to commercial insoles without a head-to-head study.

## Software

`research/statistics/methods.py`, `xstep_ml/evaluation/publication.py`, `xstep_ml/evaluation/stats.py`. Seed 67 unless overridden.
