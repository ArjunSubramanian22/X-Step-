# Reviewer B — ML methodology expert (round 2)

## Summary

Grouped CV, IID contrast, a priori hyperparameters, and leakage tests are the strongest ML parts. Metrics are now rounded and tied to a registry. High AUROC is audited rather than celebrated.

## Scores

| Novelty | Technical quality | Experimental rigor | Clarity | Significance | Confidence |
| --- | --- | --- | --- | --- | --- |
| 3 | 4 | 4 | 4 | 2 | 4 |

**Decision:** weak accept *(as a methods / evaluation paper)* / **borderline** if the venue expects patient ML.

## Major concerns

1. Task definition: 9 simulator gait classes are not a clinical endpoint.
2. Nested model selection is absent (acceptable because HPs are frozen, but then do not rank hist-GBM vs logreg).
3. Holdout robustness estimand (0.847) vs OOF (0.885) will confuse readers who miss the footnote.

## Minor concerns

1. Bootstrap n_boot=80 vs 400 inconsistency is documented but ugly.
2. No calibration slope/intercept beyond ECE.
3. Zone GBM labels are derived — correctly demoted, still easy to misuse in the repo.
