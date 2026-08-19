# Walking-data collection protocol (research planning)

This document is a **technical collection protocol** for future human walking recordings with the X-Step insole. It is **not** IRB/ethics approval, not a consent form, and not a clinical trial protocol.

Substitute recorded sessions into `make_cohort_bundle` (same `CohortBundle` fields) without changing the experiment runner.

## Identifiers

- `subject_id`: anonymous study code (no names, MRNs, or dates of birth).
- `session_id`: `{subject_id}_{YYYYMMDD}_{trial_index}` or equivalent.
- Store a separate, access-controlled linkage file **outside** this repository if re-identification is ever required by the ethics board.

## Sessions

- Repeated sessions (same day and ≥1 follow-up day when feasible) to support longitudinal features.
- Record `firmware_version`, `calibration_version`, insole serial, phone OS, app build.

## Walking protocol (suggested)

1. Unloaded baseline ADC (seated, feet off load) for 10 s.
2. Level overground walk, self-selected speed, ≥60 s or ≥40 strides per trial.
3. Optional second speed (slow) if the ethics application allows.
4. Optional sit-to-stand if relevant to the aims—do not mix unlabeled conditions in the same `session_id`.

## Calibration

- Use `data/calibration/TEMPLATE.csv`.
- If a load-cell reference is available, record commanded force, ADC, site, trial, loading vs unloading.
- Do not invent missing bench points.

## Pressure reference (optional)

If a gait-lab platform or dense insole is available, record synchronized reference peaks/PTI and the time-alignment method. Absence of a reference does not justify fabricating one.

## Synchronization

- ESP32 `t_ms` since boot in the 28-byte packet.
- Phone receive timestamp.
- If video/IMU is used, document the alignment procedure.

## Footwear and context metadata

Footwear type, sock, insole size, laterality, walking surface, indoor/outdoor, and whether the participant has neuropathy (from **approved** questionnaire/clinical record—not inferred by the app).

## Trial length and gait condition

Minimum duration as above. Label condition: level walk / slow / other. Exclusion of running unless explicitly in scope.

## Exclusion (scientific, not clinical advice)

Protocol-level examples to discuss with the ethics board: inability to walk the required duration, device size mismatch, open plantar wound if the study is limited to intact skin, inability to consent.

## Data-quality checks

- Packet `seq` monotonicity (`packet_loss_fraction`).
- ADC saturation flags.
- Unloaded baseline drift.
- Schema validation via `xstep_ml.data.schema`.
- No identifiable photos in the same pressure archive unless separately consented and stored.

## Labels

For methods papers, labels may be: gait condition, laterality, or clinician-annotated overload region. **Ulcer incidence** requires a prospective outcome protocol that this file does not provide.
