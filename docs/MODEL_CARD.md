# Model card: X-Step gait random forest and zone GBM

## Intended use
Research prototype for **pattern communication** (overload location, gait class) from four-site insoles. Not a diagnostic device. Not for autonomous treatment decisions.

## Out of scope
Wagner/University of Texas ulcer staging from pressure alone; shear; footwear-independent absolute kPa without calibration; pediatric gait; running.

## Factors
Performance is evaluated on a virtual adult walking cohort. Real FSR hysteresis, sweat, and donning error are not fully modeled.

## Metrics
Primary: macro-F1 under 5-fold GroupKFold by subject, with bootstrap 95% CI. Secondary: accuracy, McNemar vs logistic regression, noise sweep, feature ablation.

## Training data
In-silico cohort (see `docs/DATASET_CARD.md`). Optional ulcer CNN uses a public photographic DFU set with **group-wise image IDs** to reduce augmentation leakage; that task is separate.

## Ethical considerations
Alerts can cause anxiety or false reassurance. Copy is educational. Clinical endpoints require IRB-approved prospective study.

## Caveats
Do not report IID 99% toy accuracy as a clinical result. Paper numbers come from `papers/ehb2026/tables/ehb_results.json`.
