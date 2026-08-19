# EHB 2026 walking measurement protocol

This is a **technical collection protocol** for future X-Step insole walking trials.

It is **not** institutional review board (IRB) or ethics approval, **not** informed consent, and **not** a clinical trial protocol. Actual human-subject work may require IRB/ethics review and consent depending on jurisdiction, population, and intended publication. Completing this protocol does **not** constitute approval.

Do not record names, medical record numbers, dates of birth, photographs of faces, or other identifiers in the research repository. Use anonymous `subject_id` codes only.

## Purpose

Quantify within-session and between-session repeatability of four-site plantar pressure and derived features (peak pressure, pressure-time integral, contact duration, regional ratios, gait timing, overload features) during overground walking, and produce canonical recordings for subject- and session-independent ML evaluation.

## Hardware (must match freeze)

- Hardware revision: `esp32-dev-fsr402-4ch` (or a recorded successor)
- Firmware: `insole-protocol-v1` (BLE 28-byte `XS` packets, protocol v1)
- Sensors: FSR402-class at MET1, MET2, MET5, HEEL
- Nominal sample rate: **25 Hz**
- Calibration version recorded in metadata (engineering linear map until a bench curve exists)

## Per participant

Collect **multiple sessions**. Prefer:

- at least **two sessions on separate occasions** if feasible (e.g. ≥24 h apart);
- **repeated walking trials** within a session;
- enough strides to estimate within-person variability (target **≥40 strides per trial** when the walkway allows, or ≥60 s if stride counting is unavailable).

### Recommended conditions

1. Normal comfortable walking (self-selected speed)
2. Slower walking
3. Faster walking
4. Repeated walking trial of condition 1 (same session, after a seated rest)
5. Optional: alternate footwear (same speed as condition 1)

Do not mix unlabeled conditions in one `session_id`.

### Per-trial metadata (no unnecessary health information)

Record only:

| Field | Example |
|-------|---------|
| Anonymous participant ID | `S…` from the importer (never a name) |
| Session ID | `Sxxxx_20260819_01` |
| Trial index / condition | `normal`, `slow`, `fast`, `repeat_normal`, `alt_footwear` |
| Foot side | left / right / both |
| Footwear | e.g. athletic sneaker / extra-depth / other (category only) |
| Approximate walking speed | m/s if a walkway/timing gates exist; otherwise `not_measured` |
| Duration | seconds |
| Number of strides | counted or `not_counted` |
| Hardware version | `esp32-dev-fsr402-4ch` |
| Firmware version | `insole-protocol-v1` |
| Sensor calibration version | e.g. `linear_adc_engineering_v0` or a bench curve id |
| Notes | packet issues, loose insole, stop/start — no diagnoses |

Do **not** encode diagnosis, HbA1c, ulcer history, or neuropathy scores in the public research dump unless a separate ethics-approved case report form exists **outside** this repo.

## Session procedure (suggested)

1. Confirm battery, BLE advertise `XSTEP-L` / `XSTEP-R`, firmware version.
2. Seated **unloaded baseline** (feet off load) ≥10 s per foot for ADC offsets.
3. Fit insoles; 2–3 minutes quiet standing (optional notes only).
4. Walking trials as above, with rest between speed conditions.
5. Export raw ADC (+ calibrated kPa if computed on-device/host) without overwriting prior files.

Drop recordings into `data/raw/` and run `python -m research.import_real_data`.

## Quality checks

- Sequence numbers monotonic; flag packet gaps.
- Flag ADC saturations (0 or 4095 runs).
- Schema validation via `xstep_ml.data.schema`.
- Do not silently overwrite `data/raw/`.

## Analysis that this protocol enables

- Within-session repeatability (strides / repeated trials)
- Between-session repeatability (separate occasions)
- Session-independent ML splits (never share a session across train/test)
- Subject-independent ML splits (never share a subject across train/test)

Until these data exist, those analyses run only on **synthetic** traces and must be labeled as such.
