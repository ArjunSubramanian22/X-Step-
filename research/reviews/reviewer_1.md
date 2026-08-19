# Reviewer 1 — Biomedical engineering

**Score: 5 / 10** (methods paper with unspecified physical calibration)

## Strengths
- Four sites are anatomically motivated (MET1/MET2/MET5/HEEL) and pinned in firmware GPIOs.
- 12-bit ADC, 10 kΩ divider, 25 Hz, 28-byte BLE contract are documented.
- Calibration code distinguishes linear engineering map vs log–log; residuals pipeline exists.
- Simulated hysteresis/MAE/RMSE are explicitly labeled as **not** bench data.

## Major concerns
- No load-cell dataset for *this* FSR402 + divider build. Reported MAE ~1.3 N is a **simulator**.
- Linear ADC→250 kPa is not a material model of FSR402.
- No measured SNR, crosstalk, or in-shoe hysteresis.
- Repeatability ICC is generator test–retest, not human or bench.

## Minor concerns
- Temperature fields in the packet are reserved/optional and unused scientifically.
- Unloaded baseline procedure is described but not evidenced with files.

## Likely rejection reasons
Hardware paper without a calibration curve or walking traces looks like a software-only contribution.

## Required fixes (before hardware-heavy acceptance)
1. Bench calibration CSV filled from a load cell (loading/unloading, all four sites).
2. Report MAE/RMSE/relative error **on those points**, with CIs.
3. At least one real pressure trace figure (not `synthesize_window`).

## Last-mile response
Importer + template + simulated demo remain; **physical numbers were not fabricated**. Firmware/protocol freeze is recorded in `research/releases/EHB26_EXPERIMENTAL_FREEZE.md`.
