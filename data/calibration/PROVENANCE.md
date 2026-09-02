# Calibration file provenance

## Operator attestation (2026-09-01)

The experimenter states that the ADC–force pairs were **physically measured** on the four FSR sites, then sent to an LLM for table cleanup. The LLM added synthetic/generator stamps that were **not** part of the measurement.

Those stamps were removed from the canonical file after that correction. Stripping labels without this attestation would not have been enough. Independent photographs, a lab notebook, or a load-cell serial number are still **not** in the repository.

This is **not** a walking dataset and **not** a patient study.

## Canonical file

`four_site_fsr_bench.csv`

- 4 sites (MET1, MET2, MET5, HEEL)
- 5 load–unload trials
- 12 commanded forces, 0–30 N
- 480 rows
- `data_source=bench`
- Trial names `sim1`–`sim5` were renamed to `trial1`–`trial5` (the `sim` prefix came from the cleanup stamps)

## As-received archive (LLM stamps)

`four_site_pipeline_test.as_received_llm_stamps.csv`

Kept only as an audit trail of the cleanup artifact (`generator=tools/generate_simulated_calibration.py`, `data_source=simulated`). Do not use it as the paper table.

## Still required from the team (camera-ready)

- How force was applied (masses, load cell, handheld scale)
- Date and hardware revision
- Whether sensors were in the insole or on a bench fixture
