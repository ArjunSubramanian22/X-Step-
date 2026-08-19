# X-Step

Research software for **preventive diabetic foot ulcer (DFU) monitoring**: a four-site plantar insole, biomechanical features, subject-grouped machine learning, and a mobile/clinician interface.

This is an **e-health / bioengineering project** aimed at [EHB 2026](https://www.ehbconference.ro/) (wearable sensors, biosignal processing, AI in medicine, biomechanics)—not a consumer-app dump. The paper is blinded at `papers/ehb2026/manuscript_blind.md`.

## Python version (read this if pip failed)

`python3` on some Macs is still **3.7**. Current scientific stacks need **3.10+**.

```bash
bash scripts/setup_env.sh
source .venv/bin/activate
make test
make experiments    # 300 dpi figures + GroupKFold tables for the paper
```

Optional ulcer/heatmap CNNs:

```bash
WITH_DL=1 bash scripts/setup_env.sh
pip install -r requirements-dl.txt
```

## EHB 2026

| Item | Location |
| --- | --- |
| Blind manuscript | `papers/ehb2026/manuscript_blind.md` |
| Submission checklist | `papers/ehb2026/README.md` |
| Figures (300 dpi + PDF) | `papers/ehb2026/figures/` after `make experiments` |
| Tables | `papers/ehb2026/tables/` |
| Ethics / intended use | `docs/ETHICS.md` |
| Dataset card | `docs/DATASET_CARD.md` |
| Model card | `docs/MODEL_CARD.md` |
| Reproducibility | `docs/REPRODUCIBILITY.md` |

Do **not** cite IID 99% toy accuracy. Report **GroupKFold-by-subject** macro-F1 with confidence intervals from `ehb_results.json`.

## Layout

```
papers/ehb2026/  Blind manuscript, figures, tables
docs/            Dataset/model cards, ethics
xstep_ml/        Features, models, evaluation
scripts/         train_production.py, run_ehb_experiments.py, setup_env.sh
api/             FastAPI inference
mobile/          Expo app (demo + clinician snapshot)
firmware/        ESP32 BLE insole
tests/
```

## API and app

```bash
source .venv/bin/activate
python -m api.main
# other terminal
cd mobile && npm install
EXPO_PUBLIC_XSTEP_API=http://127.0.0.1:8080 npx expo start
```

## License and citation

MIT (`LICENSE`). See `CITATION.cff`. Prototype only—not a medical device.
