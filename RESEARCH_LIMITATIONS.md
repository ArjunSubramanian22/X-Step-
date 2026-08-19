# Research limitations

- **Data provenance:** gait/zone numbers in this checkout are **synthetic** unless `data_source` says otherwise.
- **No prospective outcomes:** no ulcer-prevention or amputation-reduction estimates.
- **Four FSRs** cannot reconstruct a full plantar map or shear.
- **Calibration:** firmware uses a linear ADC map; nonlinear bench calibration is unimplemented as a measured curve.
- **Zone labels** in the simulator are a function of gait class (not independent).
- **Ulcer CNN** uses public photos, possibly different populations, historically leakage-prone Roboflow splits (mitigated in `splits.py` when used).
- **Fusion** of images + pressure is **unpaired**; architecture exists, performance claims do not.
- **Battery life, BLE airtime, and on-device thermistors** are not measured in the default pipeline.
- **Sample size** of virtual subjects is a simulation parameter, not a clinical N.
- **Health index** is a specified weighted sum (engineering index), not a calibrated probability of ulceration.
- **Alert thresholds** are engineering defaults (e.g. 75 kPa), not medically validated cut-offs.
- LLM text cannot override the deterministic score and is not evidence.

These limitations are appropriate for an EHB methods paper; they are not optional footnotes.
