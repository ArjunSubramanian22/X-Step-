# X-Step: A Low-Cost Four-Site Smart Insole and Machine-Learning Framework for Continuous Plantar-Pressure Risk Monitoring in Diabetic Foot Care

**Status:** EHB 2026 manuscript skeleton (methods paper). Blind copy also lives at `papers/ehb2026/manuscript_blind.md`. **Do not paste performance numbers by hand.** After `make paper-assets`, insert `results_fragment.md` into §6.

**Validation type for current tables:** engineering / in-silico simulation (synthetic 4-FSR cohort). Not patient generalization.

## Abstract

Diabetic foot ulcers remain a major cause of hospitalization, yet peak plantar pressure and related biomechanical quantities are measurable before tissue breakdown. Dense pressure mats and research insoles capture these signals at high spatial resolution but are costly and poorly suited to unsupervised daily wear. We describe **X-Step**, a low-cost four-site force-sensitive-resistor (FSR) insole and machine-learning framework for **continuous plantar-pressure risk monitoring**. Sensors are placed at the first, second, and fifth metatarsal heads and the heel. A 25 Hz Bluetooth Low Energy stream is converted into documented biomechanical features (peak pressure, pressure-time integral, loading statistics, symmetry, cadence, and related quantities). Classical models characterize simulated overload patterns; a decomposable engineering index and threshold alerts are computed without a large language model. Because prospective insole–outcome data are not in this repository, we report **grouped, leakage-safe experiments on a virtual cohort**, plus sensor ablation, robustness to noise and packet loss, window/sampling-rate sensitivity, threshold sweeps labeled as **engineering risk-alert thresholds**, and host-side latency. These results support a **wearable methods** contribution. They do not estimate clinical ulcer-prevention rates, diagnostic accuracy in patients, or regulatory clearance.

**Keywords:** plantar pressure; diabetic foot; wearable insole; gait features; machine learning; e-health

## 1. Introduction

Peripheral neuropathy and repetitive plantar load are established mechanical ingredients of diabetic foot ulcer (DFU) risk [1–3,6]. Screening still often relies on infrequent clinic visits. Continuous monitoring exists as expensive dense arrays or as temperature-only home mats [4,5,8–11]. Sparse in-shoe FSRs can be worn daily if placement, calibration, wireless protocol, and analysis are specified well enough to reproduce.

**X-Step** targets that gap: four clinically motivated sites, an explicit 28-byte BLE payload, a canonical schema, a feature library with tests, grouped evaluation, and a mobile client for records and educational messaging. The mobile application is **not** the scientific novelty.

Questions:

1. How much 9-class overload-pattern information remains when channels are dropped (sensor ablation)?
2. How do grouped-split baselines compare (heuristic, linear, trees, ensembles)?
3. How does performance degrade under simulated noise, drift, packet loss, missing sensors, and jitter?
4. What host-side latency and model size are associated with the sklearn pipelines?

We do not ask whether the device prevents ulcers in this study.

### Contributions

1. A low-cost four-site plantar-pressure wearable architecture targeting high-risk regions.
2. An end-to-end embedded, BLE, analytics, and mobile monitoring pipeline.
3. A reproducible ML framework for pressure/gait **risk characterization** with leakage controls.
4. A systematic sensor-ablation study of the sparse configuration.
5. Robustness characterization under wearable-like perturbations.
6. Real-time **host** deployment benchmarks (radio airtime reported only when measured).

## 2. Related Work

PPP and PTI are standard mechanical markers [2,6]. IWGDF guidance stratifies risk using neuropathy, PAD, and ulcer/amputation history [7]. Contralateral skin-temperature asymmetry near 2.2 °C has been studied as a pre-ulcerative signal [8,9,11]. Footwear-based wearables and plantar systems are reviewed in [4,5]. Offloading remains central to prevention and healing [2,12]. DFU **photographs** have been classified with CNNs [10]; photos arrive after a wound exists and, in this project, are **unpaired** with insole streams.

We differ from many sparse-FSR papers by publishing a byte-level protocol, grouped rather than IID window splits, ablation/robustness, and an explicit synthetic-vs-human data contract.

## 3. System Architecture

Each insole uses four FSR402-class sensors in 10 kΩ dividers on ESP32 ADCs (MET1 GPIO34, MET2 GPIO35, MET5 GPIO32, HEEL GPIO33). Firmware streams little-endian frames: magic `XS`, version, side flags, sequence, boot-ms timestamp, four ADC samples, battery, reserved temperatures. GATT uses Nordic UART-style UUIDs. The host maps ADC to kilopascals with an **engineering linear map** until a bench curve is fitted (`xstep_ml.calibration`). The API and Expo app consume windows of shape \((T,8)\). Risk scores are deterministic; StepMate may only narrate logged factors (`research/STEPMATE_SAFETY.md`).

## 4. Methods

**Placement.** MET1, MET2, MET5, HEEL as in DFU spatial epidemiology [1,6].

**Calibration.** Divider inversion and optional log–log force; residual, repeatability, hysteresis, and drift helpers. No fabricated bench points.

**Signal processing and features.** See `research/METHODS_FEATURES.md`.

**Models.** Threshold heuristic; logistic regression; decision tree; linear SVM; random forest; gradient boosting; MLP. Production gait head: logistic regression. Zone head: GBM on **derived** simulator labels.

**Splits.** GroupKFold by virtual subject; leakage tests in `tests/test_leakage.py`.

**Evaluation and statistics.** `research/STATISTICAL_ANALYSIS_PLAN.md`.

## 5. Experiments

Baseline comparison, feature and sensor ablation, robustness, window/sampling-rate, threshold sweep, host latency, optional ulcer CNN if the public archive is present. Synthetic validation is labeled in every table. Real-data evaluation is a placeholder until `data_source=human`.

## 6. Results

Populate from generated files (do not type metrics):

```
research/manuscript/results_fragment.md
research/tables/table3_model_comparison.csv
research/tables/table4_sensor_ablation.csv
research/tables/table5_robustness.csv
research/tables/table6_system_performance.csv
```

Figures: `research/figures/fig01_architecture` … `fig12_*` (PNG/PDF/SVG). Captions state **synthetic** where applicable.

## 7. Discussion

Four sites cannot match a pressure-plate map. Ablation estimates how much simulated pattern information each region carries. Linear models competing with ensembles would indicate that PPP/PTI/asymmetry already encode the simulator’s labels—an engineering finding, not a clinical one. Robustness curves motivate better calibration and packet handling for free-living wear. Clinical implication: the system is a **decision-support / monitoring** prototype requiring prospective validation before care-pathway claims.

## 8. Limitations

See `/RESEARCH_LIMITATIONS.md`. Explicitly: synthetic data, no outcome validation, sparse sensing, unmeasured battery, unpaired images, engineering thresholds.

## 9. Conclusion

X-Step specifies a four-site insole, a reproducible feature and ML stack, and simulation-based evidence about sparse sensing, robustness, and host latency. Claims remain proportional to that evidence. Human walking data and clinical endpoints are the necessary next measurements.

## Acknowledgments / Conflict of interest

Removed for double-blind review.

## References

1. Armstrong DG, Boulton AJM, Bus SA (2017) Diabetic foot ulcers and their recurrence. N Engl J Med 376:2367–2375
2. Bus SA, van Deursen RW, Armstrong DG, Lewis J, Caravaggi CF, Cavanagh PR (2016) Footwear and offloading interventions to prevent and heal foot ulcers and reduce plantar pressure in patients with diabetes: a systematic review. Diabetes Metab Res Rev 32(S1):99–118
3. Singh N, Armstrong DG, Lipsky BA (2005) Preventing foot ulcers in patients with diabetes. JAMA 293:217–228
4. Hegde N, Bries M, Sazonov E (2016) A comparative review of footwear-based wearable systems. Electronics 5(3):48
5. Abdul Razak AH, Zayegh A, Begg RK, Wahab Y (2012) Foot plantar pressure measurement system: a review. Sensors 12:9884–9912
6. Fernando ME, Crowther RG, Pappas E, Lazzarini PA, Cunningham M, Sangla KS, Buttner P, Golledge J (2015) Plantar pressure in diabetic peripheral neuropathy patients with active foot ulceration, previous ulceration and no history of ulceration: a meta-analysis of observational studies. PLoS ONE 10(6):e0127738
7. Schaper NC, van Netten JJ, Apelqvist J, Bus SA, Hinchliffe RJ, Lipsky BA (2023) Practical guidelines on the prevention and management of diabetes-related foot disease (IWGDF 2023 update). Diabetes Metab Res Rev 40:e3657
8. Armstrong DG, Holtz-Neiderer K, Wendel C, Mohler MJ, Kimbriel HR, Lavery LA (2007) Skin temperature monitoring reduces the risk for diabetic foot ulceration in high-risk patients. Am J Med 120:1042–1046
9. Frykberg RG, Gordon IL, Reyzelman AM, et al. (2017) Feasibility and efficacy of a smart mat technology to predict development of diabetic plantar ulcers. Diabetes Care 40:973–980
10. Goyal M, Reeves ND, Rajbhandari S, Yap MH (2018) Fully convolutional networks for diabetic foot ulcer segmentation. (DFU image analysis literature; optional CNN uses a public photographic set only)
11. Lavery LA, Higgins KR, Lanctot DR, et al. (2007) Preventing diabetic foot ulcer recurrence in high-risk patients: use of temperature monitoring as a self-assessment tool. Diabetes Care 30:14–20
12. Cavanagh PR, Bus SA (2010) Off-loading the diabetic foot for ulcer prevention and healing. J Vasc Surg 52:37S–43S

Verify each citation against the publisher PDF before camera-ready. Do not add unverified DOIs.
