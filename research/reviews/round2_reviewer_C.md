# Reviewer C — wearable systems expert (round 2)

## Summary

The 25 Hz / 28-byte / ESP32 contract is reviewer-usable. Host latency is honest. Missing radio, power, and packaging measurements remain disqualifying for a “wearable deployment” claim if overstated. The paper now states they are unmeasured.

## Scores

| Novelty | Technical quality | Experimental rigor | Clarity | Significance | Confidence |
| --- | --- | --- | --- | --- | --- |
| 3 | 3 | 3 | 4 | 3 | 4 |

**Decision:** weak reject if sold as a deployed wearable; **borderline** as an architecture+host-timing methods paper.

## Major concerns

1. No current draw, no coin-cell vs LiPo, no BLE connection interval / notify size on air.
2. Packet loss is zero-fill in numpy, not CRC/timeout traces.
3. Mechanical coupling of FSR402 in a shoe is unspecified (foam, hysteresis, walking speed).

## Minor concerns

1. Two-insole fusion assumed perfect clock alignment.
2. Battery byte in the packet is unused scientifically.
3. Random forest 13 ms inference is a useful negative result; keep it.
