# Leakage audit

Date: 2026-08-19. No model was retrained for this audit.

## Protocols

| Protocol | File | Finding |
| --- | --- | --- |
| GroupKFold by subject (primary) | `research/results/splits/subject_groupkfold.json` | Train/test indices disjoint; subject IDs disjoint (unit test) |
| GroupKFold by session | `session_groupkfold.json` | Indices disjoint |
| LOSO | `loso_subject.json` | Subject holdout by construction |
| IID window | `iid_window.json` | **Subject leakage possible by design**; reported as optimistic control (F1 0.931 vs 0.885) |

## Checks performed

1. **Duplicate windows across grouped folds.** On a smaller `make_cohort` draw, exact rounded-window duplicates did not cross GroupKFold partitions. Frozen 2592-window uniqueness is not a clinical identity check; it is a generator check.
2. **Preprocessing before split.** `StandardScaler` is inside `Pipeline` and fit on training folds only (`xstep_ml.evaluation.baselines`). A unit test asserts full-data scaler means differ from train-only means.
3. **Hyperparameter search on test.** Hyperparameters are a priori (`HYPERPARAMETERS.md`). `baseline_models()` does not take `X_test`.
4. **Thresholds on test.** Peak cut-offs are engineering defaults (75 kPa), not Youden-optimized on the paper test set as a claimed clinical threshold. `threshold_sweep.csv` is an operating-point table on synthetic labels.
5. **Zone labels.** Derived from gait class in the simulator — not an independent annotation. Stated in Methods.
6. **Ulcer images.** Out of primary paper; not mixed into plantar tables.

## Known optimistic number

IID macro-F1 **0.931** must not replace grouped **0.885**.

## Residual risk

Synthetic subjects share a generative family. Grouped CV blocks **identity leakage** of the virtual subject ID, not all simulator-family leakage. That is a limitation, not hidden.
