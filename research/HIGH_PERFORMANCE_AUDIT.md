# High-performance audit

Any metric ≳ 0.98, and any 9-class macro-F1 ≳ 0.88 on a wearable task, is treated as suspicious until explained.

| Metric | Value | Why it looks high | Verdict |
| --- | --- | --- | --- |
| Logreg OOF AUROC | 0.979 | 9-class one-vs-rest on a simulator | **Plausible for the generator, not for patients.** Feature ablation: peak-only F1 0.886 ≈ full 59-D 0.885, so labels are largely peak-separable by construction. |
| Logreg grouped macro-F1 | 0.885 | Strong for 9 classes | Same explanation: class-conditional peaks. Still far from 1.0; `normal` and `shuffle` dominate errors (`ERROR_ANALYSIS.md`). |
| Hist-GBM F1 | 0.885 | Ties logreg | Not celebrated as superiority; CIs overlap. |
| IID F1 | 0.931 | Higher than grouped | **Optimistic protocol**, not headline. |
| Holdout F1 at noise 1.5–3.5 kPa | 0.88 > baseline 0.847 | Mild extra noise vs a baseline already trained with 3.5 kPa | Do **not** claim noise helps; report 12 kPa failure (0.641). |
| Specificity macro | 0.986 | Many true negatives in one-vs-rest style aggregations | Secondary; not a DFU-screening claim. |
| Host latency | 0.23 ms | Looks “too fast” | Expected for 59-D logreg on a laptop CPU; not radio time. |

## Checks that did **not** explain the AUROC as a bug

- Subject IDs do not overlap in grouped folds (leakage audit).
- Features are not the class integer itself; they are PPP/PTI/gait descriptors.
- Majority dummy F1 is 0.040 — the task is not a single majority class.

## What we refuse to write

“Highly accurate,” “clinical-grade,” or “0.98 AUROC in patients.”
