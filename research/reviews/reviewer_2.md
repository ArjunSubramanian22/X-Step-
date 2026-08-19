# Reviewer 2 — Machine learning

**Score: 6.5 / 10**

## Strengths
- GroupKFold by subject; leakage tests; IID vs session vs subject comparison exists.
- Baselines share a priori hyperparameters (no one-model grid search on test).
- Sensor ablation, OOF probabilities (AUROC/Brier/ECE), Platt on **inner** groups.
- Bootstrap CIs; McNemar exploratory; error analysis by class and peak tertile.
- Split definitions dumped to `research/results/splits/`.

## Major concerns
- Labels are simulator classes, not clinical events. High macro-F1 is **not** DFU detection.
- Zone labels are a function of gait class (leakage of label construction).
- Frozen table3 CIs used n_boot=80 (SAP preferred 400).
- Feature count stays 59 when sensors are zeroed (honest but easy to misread).

## Minor concerns
- MLP `early_stopping=False` is a sklearn string-label workaround.
- Production artifact still named `gait_pattern_rf.joblib`.

## Likely rejection reasons
“We beat RF with logreg on synthetic sinusoids” is not a learning contribution unless framed as methods/engineering.

## Required fixes
Keep synthetic labels explicit in every table. Do not tune on the final test subjects. Report CI overlap rather than ranking 0.885 vs 0.885.

## Last-mile response
OOF `predict_proba`, reliability diagram, split-protocol table, extra 2-site ablation, packet-loss 1–30%, and error analysis were added. Human grouped evaluation still **blocked on data**.
