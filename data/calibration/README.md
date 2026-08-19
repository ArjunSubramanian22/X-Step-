# FSR calibration data

Physical (force, ADC) pairs for this device are **not** in the repository.

- `TEMPLATE.csv` — columns to fill after a bench session.
- `SIMULATED_example.csv` — **not measurements**; produced by `xstep_ml.calibration.simulate_example_curve`.

Pipeline: ADC → divider resistance → optional log–log force → pressure via assumed contact area. The firmware still uses a linear ADC→kPa engineering map until a bench curve is fitted.
