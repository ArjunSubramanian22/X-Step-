# X-Step ESP32 insole firmware

Flashes the 28-byte BLE protocol used by `xstep_ml/protocol.py` and the mobile app.

## Hardware

| Site | FSR | ESP32 ADC |
|------|-----|-----------|
| 1st metatarsal | FSR402 | GPIO34 |
| 2nd metatarsal | FSR402 | GPIO35 |
| 5th metatarsal | FSR402 | GPIO32 |
| Heel | FSR402 | GPIO33 |

Each FSR is a voltage divider with **10 kΩ** to ground. 3.3 V rail.

Build two boards: left (`INSOLE_SIDE_LEFT 1`, advertises `XSTEP-L`) and right (`0`, `XSTEP-R`).

## Build

Arduino IDE 2 or PlatformIO, board **ESP32 Dev Module**, partition default, PSRAM off.

Calibrate unloaded ADC in the app onboarding screen; the API subtracts that baseline before kPa conversion.
