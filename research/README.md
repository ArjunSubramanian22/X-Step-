# X-Step research

**Title.** X-Step: A Low-Cost Four-Site Smart Insole and Machine-Learning Framework for Continuous Plantar-Pressure Risk Monitoring in Diabetic Foot Care

## Research question

Can a **four-site** FSR insole, with clinically motivated placement (MET1, MET2, MET5, HEEL), a documented BLE contract, and a leakage-safe ML pipeline, support **biomechanical risk characterization** (overload pattern, regional load, engineering alerts) under realistic sensor imperfections—without claiming unmeasured clinical outcomes?

## Hypothesis

Sparse sensors at high-risk plantar regions retain enough information for engineering discrimination of simulated overload patterns, with graceful (measurable) degradation under noise, packet loss, missing channels, and calibration drift. Four sites are expected to outperform one- and two-site subsets on that synthetic task; this is **not** a hypothesis about ulcer incidence.

## Contributions (intended paper)

1. Low-cost four-site wearable architecture targeting high-risk plantar regions.
2. End-to-end embedded → BLE → analytics → mobile pipeline (app is a client, not the novelty).
3. Reproducible ML framework for pressure/gait **risk characterization** on grouped splits.
4. Sensor-ablation quantifying information retained by the sparse configuration.
5. Robustness under noise, packet loss, drift, and missing sensors.
6. Host-side latency/size benchmarks for wearable-feasible inference.

Do **not** claim clinical ulcer prediction, prevention rates, or FDA status.

## Dataset status

| Dataset | Status |
| --- | --- |
| In-silico 4-FSR gait cohort | **Available** (`xstep_ml.data.synthetic_gait`) — **engineering/simulation validation only** |
| Physical FSR bench calibration | **Not in repo** — pipeline + simulated example only |
| Human walking traces | **Not in repo** — see `protocols/REAL_DATA_PROTOCOL.md` (not IRB approval) |
| Public DFU photographs | Optional, gitignored; unpaired with insole data |

## Experimental design

Subject-grouped (and session-grouped) splits. Baselines include a threshold heuristic, logistic regression, trees/ensembles, and linear SVM. Ablations: sensors, feature groups, model class. Robustness perturbations are simulated. Window length and sampling rate are swept. Overload thresholds are labeled **engineering risk-alert thresholds**.

## Evaluation

Publication metrics (accuracy, balanced accuracy, precision, recall, specificity, F1, AUROC/PR-AUC when probabilities exist, Brier/ECE when valid) with bootstrap 95% CIs. Results are written to `research/results/` and `research/tables/`. Manuscript numbers must be injected from those files.

## Commands

```bash
bash scripts/setup_env.sh
source .venv/bin/activate
make test
RESEARCH_SMOKE=1 make ci-local     # fast
make paper-assets                  # full experiments + figures + tables
```

## Figures and tables

Generated under `research/figures/` (PNG/PDF/SVG) and `research/tables/`. Captions mark synthetic data.

## Current limitations

See `/RESEARCH_LIMITATIONS.md`. Synthetic labels are not patient generalization.

## Next clinical-validation step

Collect de-identified walking sessions per `protocols/REAL_DATA_PROTOCOL.md` under an appropriate ethics review, then **substitute** human loaders into `make_cohort_bundle` without changing the experiment runner.
