# Power measurement protocol

No battery or current measurements exist in this repository. **Do not invent runtime.**

This protocol is for a future bench measurement so a wearable paper can report idle, sensing, BLE streaming, average operating power, and estimated runtime.

It is not a claim that X-Step has been characterized for battery life.

## Equipment (suggested)

- DC power analyzer or USB power meter on the 5 V / 3.3 V rail actually supplying the ESP32 + FSR dividers
- Fully charged battery of the same type used in the wearable build (record capacity mAh and chemistry)
- Phone or BLE sniffer only as the **receiver**; do not use phone battery as a proxy for insole power

## Conditions (record each for ≥60 s after settling)

| Condition | What is enabled |
|-----------|-----------------|
| Idle | MCU awake, FSRs powered, BLE advertising, **no** notify stream |
| Sensing only | ADC loop at 25 Hz, BLE advertising, notifications **off** if the firmware allows |
| BLE streaming | 25 Hz notify of 28-byte packets to a connected central (typical phone) |
| Average operating | Sensing + BLE streaming as in intended use (both insoles if dual-rail) |

Repeat each condition ≥3 times. Report mean, SD, and if possible 95% CI.

## Derived runtime (only after measuring current)

\[
t_{\mathrm{hours}} \approx \frac{C_{\mathrm{mAh}} \times \eta}{I_{\mathrm{avg,mA}}}
\]

State battery capacity, derating \(\eta\) (or set \(\eta=1\) and call it a **upper bound**), and that footwear temperature and TX power will change the result.

## Out of scope until measured

- Hours per charge
- Comparison to commercial insoles
- “All-day” marketing claims

Store CSVs under `data/raw/power/` with timestamps; never overwrite raw files. The importer does not consume power logs (analysis is spreadsheet/script based).
