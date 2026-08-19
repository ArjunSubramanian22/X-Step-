# Canonical raw session schema

Each session is a directory under `data/raw/<session_folder>/`.

## Required metadata: `session.json`

```json
{
  "subject_id": "optional-study-code",
  "session_id": "sess001",
  "foot_side": "both",
  "footwear": "athletic",
  "hardware_revision": "esp32-dev-fsr402-4ch",
  "firmware_version": "insole-protocol-v1",
  "calibration_version": "linear_adc_engineering_v0",
  "sample_hz": 25,
  "notes": ""
}
```

`subject_id` is hashed to an anonymous `S…` code. Original names must not appear in git.

## Traces: `traces.csv` (preferred)

Columns:

`timestamp_ns,seq,foot_side,met1_adc,met2_adc,met5_adc,heel_adc`

Optional calibrated columns: `met1_kpa,met2_kpa,met5_kpa,heel_kpa`.

`foot_side` is `left` or `right`. Bilateral capture uses two files (`traces_left.csv`, `traces_right.csv`) or interleaved rows.

## Optional: concatenated BLE payloads

`packets.ble.bin` — concatenated 28-byte `XS` packets as defined in `xstep_ml/protocol.py`.

## Optional: window JSON

`windows.json` — list of `PressureWindowRecord` objects (canonical ML schema).
