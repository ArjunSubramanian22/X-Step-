# Frozen model hyperparameters

Selection protocol: **a priori defaults** in `xstep_ml.evaluation.baselines.baseline_models`. No grid search on the evaluation set. The same `random_state=67` is used for every sklearn estimator that accepts a seed.

These values are the EHB freeze. Changing them requires a new freeze SHA.

| Model | Hyperparameters |
|-------|-----------------|
| threshold_heuristic | `peak_normal_kpa=70`, `shuffle_cadence=88`, `asym_cut=0.42` (engineering rule, not fitted) |
| majority | `DummyClassifier(strategy="most_frequent")` |
| logreg | `StandardScaler` + `LogisticRegression(max_iter=400, class_weight="balanced")` |
| decision_tree | `max_depth=8`, `min_samples_leaf=6`, `class_weight="balanced"` |
| linear_svm | `StandardScaler` + `LinearSVC(class_weight="balanced", dual=False, max_iter=4000)` |
| random_forest | `n_estimators=160`, `max_depth=12`, `min_samples_leaf=4`, `class_weight="balanced"`, `n_jobs=-1` |
| gbm | `n_estimators=80`, `max_depth=3`, `learning_rate=0.08` |
| mlp | `hidden_layer_sizes=(64, 32)`, `max_iter=80`, `early_stopping=False` |
| hist_gbm | `max_depth=3`, `learning_rate=0.08`, `max_iter=80` |

Probability calibration (Platt / isotonic), if applied, uses **inner validation groups from the training fold only** (`cv='prefit'` on a group hold-out). The outer test subjects are never used to fit a calibrator.
