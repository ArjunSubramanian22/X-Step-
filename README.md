# X-Step

Research software for a **four-site plantar-pressure insole** and a leakage-safe machine-learning framework for **continuous biomechanical risk monitoring** in diabetic foot care.

**Paper title:** *X-Step: A Low-Cost Four-Site Smart Insole and Machine-Learning Framework for Continuous Plantar-Pressure Risk Monitoring in Diabetic Foot Care*

Target venue: [EHB 2026](https://www.ehbconference.ro/) (wearables, biosignals, AI in medicine, biomechanics). This repository is a **methods / biomedical-engineering** project. It is **not** a medical device, not FDA-cleared, and not a claim that ulcers or amputations are prevented.

Current quantitative gait/zone tables are **engineering/simulation validation** on a synthetic 4-FSR cohort unless a result file says `data_source=human`.

## Research contribution

1. Low-cost four-site sensing at MET1, MET2, MET5, and HEEL  
2. Embedded → BLE → feature/ML → mobile pipeline (the app is a client)  
3. Reproducible grouped-split ML for overload-pattern **characterization**  
4. Sensor ablation, robustness, threshold sweeps, host latency  

Details: [`research/README.md`](research/README.md) · manuscript [`research/manuscript/main.md`](research/manuscript/main.md)

```
FSR ×4  →  ESP32  →  BLE (28 B "XS")  →  features / sklearn  →  engineering alerts
                                              └─ Expo app (record + educational chat)
```

## Repository structure

```
research/          SAP, experiments, figures, tables, manuscript
xstep_ml/          schema, calibration, features, models, evaluation
firmware/          ESP32 insole
api/               FastAPI inference (deterministic score; LLM does not set risk)
mobile/            Expo client
data/              schemas; no PHI
models/            model card (artifacts in artifacts/)
tests/
```

## Quickstart

Python **3.10+** required (`python3` on some Macs is 3.7).

```bash
bash scripts/setup_env.sh
source .venv/bin/activate
make test
RESEARCH_SMOKE=1 python research/experiments/run_research.py
make figures
```

Full paper assets (slower):

```bash
make paper-assets
```

API + app:

```bash
python -m api.main
# other terminal
cd mobile && npm install && npx tsc --noEmit
EXPO_PUBLIC_XSTEP_API=http://127.0.0.1:8080 npx expo start
```

## Reproducibility

See [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md). Manifests: `research/results/manifest.json`. Seed 67.

## Current results

After experiments, read `research/tables/table3_model_comparison.csv` and `research/manuscript/results_fragment.md`. **Do not** cite IID window accuracy as the paper result.

## Dataset disclosure

| Data | In this repo? |
| --- | --- |
| Synthetic 4-FSR windows | generated |
| Bench FSR calibration measurements | no (pipeline + simulated example only) |
| Human walking / clinical outcomes | no |
| Public DFU photos | optional, gitignored, unpaired |

## Limitations and clinical disclaimer

[`RESEARCH_LIMITATIONS.md`](RESEARCH_LIMITATIONS.md) · [`docs/ETHICS.md`](docs/ETHICS.md)

Software provides **risk monitoring / decision-support prototypes**. It does not diagnose disease, detect infection, or guarantee prevention. Prospective clinical validation is required before care-pathway claims.

## Citation

See `CITATION.cff`. Paper status: **draft / not yet submitted**. Blind manuscript notes: `papers/ehb2026/`.

## License

MIT (`LICENSE`).
