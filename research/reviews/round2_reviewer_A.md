# Reviewer A — skeptical biomedical engineer (round 2)

**Manuscript reviewed:** `research/manuscript/main.md` (post-hardening draft).

## Summary

A four-site FSR insole is specified and evaluated with synthetic overload-pattern labels, ablation, and host latency. The hardware story is coherent. The absence of even one instrumented walking trial is still the dominant scientific gap.

## Scores (1–5)

| Novelty | Technical quality | Experimental rigor | Clarity | Significance | Confidence |
| --- | --- | --- | --- | --- | --- |
| 3 | 4 | 3 | 4 | 3 | 4 |

**Decision:** borderline

## Major concerns

1. All classification evidence is a simulator whose labels are largely peak-separable (peak-only ≈ full features). That is disclosed, but it caps significance.
2. Calibration MAE is a software demo, not a load-cell on FSR402 + 10 kΩ + ESP32 ADC.
3. BLE is a byte layout, not a measured link.

## Minor concerns

1. Fig. 4 illustrative traces may not match 25 Hz.
2. 75 kPa alert is arbitrary relative to 200 kPa literature bands.
3. App alias paragraph is easy to skip; a reviewer may still think there are eight anatomical sites.
