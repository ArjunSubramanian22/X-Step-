# X-Step

Preventive diabetic foot ulcer system: **custom 4-FSR smart insoles**, **real-time gait/pressure ML**, **wound-image grading**, and a **mobile + clinician app**.

This repository is the production monorepo for hardware firmware, on-device and server ML, the Expo app, and the inference API.

## What the product actually does

| Claim | How it is implemented |
| --- | --- |
| 4 sensors at 1st, 2nd, 5th metatarsal + heel | `xstep_ml/hardware.py`, ESP32 firmware, foot map labels |
| BLE microcontroller → phone | 28-byte packet in `xstep_ml/protocol.py` / `mobile/services/protocol.ts` |
| Abnormal pressure → immediate posture alert | Threshold + gait-pattern alerts in the app |
| Daily pressure graphs for clinicians | Trends tab + Clinician report screen |
| ML gait / asymmetry | Random forest on biomechanical features (cadence, PTI, peak, L/R asymmetry) |
| Wound photo → severity | Ulcer CNN (`UlcerNN` / transfer learning) via `POST /v1/ulcer` |
| Personalized recommendations | Rule engine grounded in sensor facts + StepMate prompt |
| Offline | Phone-side gait engine if the API is down |

## Layout

```
mobile/          Expo / React Native app (X-Step)
api/             FastAPI production inference
xstep_ml/        Training + inference library
firmware/        ESP32 insole sketch
artifacts/       Shipped gait / zone models
scripts/         Train & eval
ulcer model/     Legacy notebooks + ulcer CNN weights
heatmap model/   Legacy plantar-heatmap CNN
```

## Run the ML API

```bash
python3 -m pip install -r requirements.txt
python3 scripts/train_production.py   # writes artifacts/
python3 -m api.main                   # http://127.0.0.1:8080
```

- `GET /health`
- `POST /v1/analyze` — window of 8-channel kPa frames
- `POST /v1/ulcer` — wound image
- `POST /v1/packet/decode` — BLE hex

```bash
docker build -t xstep-api .
docker run -p 8080:8080 xstep-api
```

## Run the app

```bash
cd mobile
npm install
EXPO_PUBLIC_XSTEP_API=http://127.0.0.1:8080 npx expo start
```

Without hardware, the walking simulator streams physiologic 4-FSR gait (including periodic forefoot-overload demos) so alerts, graphs, and ML stay live.

## Train other models

```bash
python3 scripts/train_ulcer.py --architecture efficientnet_b0 --loss ordinal --epochs 50 --gradcam
python3 scripts/train_heatmap.py --architecture resnet50 --cv-folds 5
```

## Tests

```bash
python3 -m pytest tests -q
```

Not a medical device in this repository form: models support prevention workflows and clinician review. They do not diagnose or replace in-person care.
