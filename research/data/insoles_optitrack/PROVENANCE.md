# Insoles + OptiTrack walking archive

**This is not X-Step four-site FSR402 walking.**

Operator-provided file: `InsolesOpitrackDataset.zip` (local path used at ingest: the operator Downloads copy). File layout matches the public record:

- Zenodo: [10.5281/zenodo.20156243](https://doi.org/10.5281/zenodo.20156243)
- Software stack cited in that record: MVP-GAIT
- Hardware: 32 pressure channels per foot (`PressureSensor 0`–`31`, native counts 0–4096), IMU, CoP, `sumP`, plus OptiTrack Baseline Lower (20 markers)

Do **not** describe these traces as the ESP32 4×FSR402 prototype, 25 Hz `XS` packets, or calibrated X-Step kPa.

## What is stored in git

- Layout map: `sensor_layout.json` (anatomical clusters digitized from `insoles-number.jpeg`)
- Derived summaries: `research/results/human_optitrack_evaluation.json`, `research/tables/human_optitrack_*.csv`
- The 84 MB zip and raw per-take CSVs are **not** committed (`data/raw/` is gitignored)

## Analysis

```text
python -m research.experiments.evaluate_insoles_optitrack
```

Looks for `XSTEP_OPTITRACK_ZIP`, then `data/raw/InsolesOpitrackDataset.zip`, then `~/Downloads/InsolesOpitrackDataset.zip`.

## Exclusions (from `info.txt` in the zip)

- P13 M1: insole desynchronization — excluded from pressure analysis
- P3 M8: OptiTrack errors, not locally interpolable — excluded from mocap speed
- `.I` folders: OptiTrack gap repair only; pressure is not double-counted

## Ethics

No IRB or consent form is inside the zip. Do not invent an approval number. Confirm sharing language before promising a public dump from this repository (the matching Zenodo record is already public).
