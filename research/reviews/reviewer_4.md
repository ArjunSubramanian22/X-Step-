# Reviewer 4 — Wearable systems

**Score: 5 / 10**

## Strengths
- Byte-level BLE payload and 25 Hz loop are specified.
- Host decode / features / logreg latency with mean, P95, P99.
- Packet-loss **simulation** curve 0–30%; sampling-rate tradeoff without upsampling.
- Power **protocol** exists so runtime is not invented.
- Dual-insole naming and GATT UUIDs documented.

## Major concerns
- BLE airtime, connection interval, and field packet loss are **unmeasured**.
- No current-draw or battery runtime.
- Host CPU latency ≠ wearable latency (phone + radio + UI).
- Earlier “host alert path” averaged RF (~12 ms) with logreg; last-mile reports **logreg-only** host path.

## Minor concerns
- 28 bytes × 2 feet × 25 Hz ≈ 1.4 kB/s is a design estimate, not a sniffer measurement.
- No firmware watchdog / CRC beyond magic `XS`.

## Likely rejection reasons
“Real-time wearable” without radio or power numbers is a common EHB objection.

## Required fixes
Instrument notify timestamps on phone vs ESP32 `t_ms`; measure rail current per the power protocol.

## Last-mile response
Latency breakdown figure uses host stages only; radio/battery rows stay empty rather than fabricated.
