# X-Step: Sparse Four-Site Plantar-Pressure Sensing for Continuous Risk Monitoring—Methods, Ablation, and Wearable Deployment Characterization

**Status:** EHB 2026 methods manuscript. Quantitative Results are generated from frozen files (`research/manuscript/generated_results.md`). Do not paste metrics by hand.

**Validation type in this checkout:** engineering / in-silico simulation on a synthetic 4-FSR cohort. **Zero human walking sessions** are stored in the repository.

## Abstract

**Problem.** Continuous plantar-pressure monitoring is relevant to diabetic foot mechanics, but dense arrays are costly and often confined to the laboratory. Sparse wearables need evidence that a handful of sites still carry usable biomechanical information, and that models remain usable under sensor and radio imperfections.

**System.** X-Step is a low-cost insole with four force-sensitive resistors at the first, second, and fifth metatarsal heads and the heel, sampled at 25 Hz on an ESP32 and streamed as a documented 28-byte Bluetooth Low Energy payload.

**Contribution.** We specify the hardware contract, a 59-dimensional biomechanical feature set, grouped (subject- and session-level) evaluation, classical ML baselines with a priori hyperparameters, sensor ablation, perturbation robustness, sampling-rate and window tradeoffs, and host-side latency. A mobile app and optional chat layer are supporting infrastructure; they do not define risk.

**Evaluation.** All numerical ML results in this checkout use a 24-virtual-subject synthetic gait cohort (2592 windows) with GroupKFold by subject. Physical calibration, BLE airtime, battery, and human walking data are **not** in the result tables.

**What the results establish.** On this simulator, four-site logistic regression recovers overload-pattern labels with high grouped macro-F1; dropping heel or fifth-metatarsal channels loses substantial information; host feature+logreg latency is well below the 40 ms sample period; 30% simulated packet loss and large sensor bias degrade performance. The work does **not** establish ulcer prediction, diagnosis, prevention, or patient generalization.

**Keywords:** plantar pressure; sparse sensing; wearable insole; gait features; robustness; e-health

## 1. Introduction

Repetitive plantar load and neuropathy are established mechanical ingredients of diabetic foot ulcer (DFU) risk [1–3,6]. Clinic visits sample that load infrequently. Dense mats and research insoles map the foot at high spatial resolution [5] but are poorly matched to unsupervised daily wear. Temperature-based home tools have RCT evidence for a different modality [8–10]. Footwear wearables are reviewed in [4,12].

**Research gaps**

1. Dense plantar systems provide spatial maps at greater hardware complexity and cost; sparse low-cost FSRs need **quantitative** evidence of what information remains when channels are removed.
2. Wearable ML papers often report IID window accuracy. Subject- and session-independent splits are required to avoid mixing a person’s strides across train and test.
3. Deployment constraints—noise, calibration drift, missing channels, packet loss, sampling rate, and host latency—are rarely reported as operating curves rather than a single accuracy number.

X-Step addresses these **engineering** questions. The mobile application records streams and displays deterministic scores; it is not the scientific novelty. StepMate, if present, may only narrate already-computed factors [see `research/STEPMATE_SAFETY.md`].

We ask:

> Can a sparse, low-cost four-site smart insole preserve sufficient plantar biomechanical information for continuous pressure-risk monitoring while remaining robust and computationally practical for real-time wearable deployment?

We do not ask, in this study, whether the device prevents ulcers or amputations.

### Contributions

1. Design of a low-cost four-site plantar-pressure smart insole targeting biomechanically relevant regions (MET1, MET2, MET5, HEEL) for continuous monitoring.
2. A reproducible end-to-end pipeline from embedded ADC and BLE transmission to gait/pressure features and real-time **risk characterization** (engineering index and alerts).
3. Systematic evaluation of sparse placement using sensor-ablation experiments and classical ML baselines under leakage-safe grouped splits.
4. Robustness characterization under wearable-like failure modes: sensor noise, bias, calibration drift, missing channels, timing jitter, and packet loss.
5. Real-time **host** deployment characterization (feature extraction and inference latency, model size). Radio airtime and battery are specified as unmeasured.

## 2. Related work

Peak plantar pressure (PPP) and pressure-time integral (PTI) are standard mechanical markers [2,6]. IWGDF practical guidelines (2023 update) stratify clinical risk using neuropathy, PAD, and ulcer history—not a four-FSR classifier [7]. Offloading remains central to prevention and healing [2,12].

Table `research/tables/related_systems.csv` compares modalities **only** using cited facts. We do **not** claim that X-Step is more accurate than Pedar-class arrays, SmartStep, or temperature RCTs. The intended gap is a **documented sparse pressure pipeline** with ablation, grouped ML, and robustness—not a new RCT.

DFU **photographs** are a separate literature. An optional public-image CNN exists in this repository but is **not** part of the primary paper (`research/manuscript/SUPPLEMENTARY_ULCER.md`).

## 3. System architecture

Each insole uses four FSR402-class sensors in 10 kΩ dividers on ESP32 12-bit ADCs: MET1 GPIO34, MET2 GPIO35, MET5 GPIO32, HEEL GPIO33. Firmware (`firmware/xstep_insole/xstep_insole.ino`) samples at **25 Hz** and notifies a 28-byte little-endian frame: magic `XS`, protocol version 1, side flags, sequence, boot-ms timestamp, four ADC samples, battery, reserved temperatures. GATT uses Nordic UART-style UUIDs. Two insoles (`XSTEP-L`, `XSTEP-R`) are fused on the host into shape \((T,8)\).

Engineering pressure uses a linear ADC→kPa map (250 kPa full scale after unloaded baseline). This is **not** a fitted bench curve. Research code can fit log–log force models when load-cell files exist (`xstep_ml.calibration`).

Risk scores and alerts are deterministic (`xstep_ml.inference`). An LLM must not set the score.

## 4. Methods

**Placement.** MET1, MET2, MET5, HEEL, motivated by DFU spatial epidemiology [1,6], not by an optimization over a dense map in this study.

**Calibration procedure.** Unloaded baseline ADC; optional load-cell CSV (`data/calibration/TEMPLATE.csv`). Residual, CV, hysteresis, and drift helpers are implemented. No fabricated bench points. Sensor calibration error ≠ classification accuracy.

**BLE protocol.** See `xstep_ml/protocol.py` (28 bytes, v1).

**Preprocessing.** Non-negative kPa windows; packet-loss fraction from sequence gaps after import.

**Segmentation.** Frozen experiments use **fixed 4 s windows** at 25 Hz (100 samples), not stride-cut events. A window/fs grid is reported. Approximately one stride at 120 steps/min is ~0.5 s; 4 s spans several steps for cadence/PTI stability versus alert delay.

**Features.** 59 names in `xstep_ml.biomechanics.FEATURE_NAMES`: per-site peak/mean/PTI/load/high/CV (left/right), asymmetry, cadence, stance ratio, COP-AP, forefoot share, peak_any, pti_total. Tests in `tests/test_features.py`.

**Models and hyperparameters.** A priori (`research/configs/HYPERPARAMETERS.md`): threshold heuristic, majority dummy, logistic regression (production gait head), decision tree, linear SVM, random forest, GBM, MLP, hist-GBM. Zone GBM uses **derived** simulator labels. No test-set hyperparameter search.

**Splits.** GroupKFold by `subject_id` (primary); GroupKFold by `session_id`; IID StratifiedKFold as an **optimistic** control; leave-one-subject-out when \(N\) allows. Split index files: `research/results/splits/`. Leakage tests fail on overlapping IDs.

**Statistics.** Macro-F1 primary; balanced accuracy, precision/recall/specificity, confusion matrices; AUROC/PR-AUC/Brier/ECE when probabilities exist. Percentile bootstrap 95% CIs. McNemar on paired OOF is exploratory. Effect size = Δmacro-F1 and CI overlap, not p-value theater. SAP: `research/STATISTICAL_ANALYSIS_PLAN.md`.

**Thresholds.** Peak cut-offs are **engineering risk-alert operating points** on synthetic non-normal vs normal labels.

## 5. Experiments

See `research/releases/EHB26_EXPERIMENTAL_FREEZE.md`. Commands: `make test`, `make experiments`, `make final-eval`, `make figures`, `make generated-results`.

Human import: `python -m research.import_real_data` from `data/raw/` (empty in this checkout).

## 6. Results

Insert the generated file (do not retype numbers):

```
research/manuscript/generated_results.md
```

Figures (PNG/PDF/SVG): fig01 architecture, fig02 placement, fig03 pipeline, fig04 simulated pressure, fig05 calibration (simulated), fig06 grouped confusion, fig07 models, fig08 ablation, fig09 noise, fig10 packet loss, fig11 host latency, fig12 repeatability (simulator), fig13 sampling rate. Captions state synthetic where applicable.

## 7. Discussion

**Why four sensors?** Ablation on this simulator shows that some three-site subsets (especially those that drop MET5 or heel) lose a large fraction of overload-pattern information, while some other three-site subsets stay closer to four-site performance. Single-site models are weak. We therefore describe four sites as a **reasonable cost/information tradeoff for these labels**, not as a globally optimal layout and not as a clinical standard.

**Does it generalize?** Subject-grouped CV is mandatory in the tables. Session-grouped vs IID comparison is reported so optimistic window mixing cannot be mistaken for deployment performance. There are **no unseen human participants** in this checkout.

**Is it robust?** Noise, packet loss, missing channels, and bias sweeps show operating regions and failure (e.g. large constant bias). Packet loss is **simulated**, not measured over the air.

**Is it deployable?** Host feature+logreg time is small compared with the 40 ms sample period. BLE radio time, packet loss in the field, memory on-device, and battery are **not** demonstrated until measured.

**Is it clinically proven?** Biomechanical monitoring is **not** prospective proof of DFU prevention. No diagnostic claim is made.

**What comes next?** Load-cell calibration of this hardware; instrumented BLE/power; ethics-approved walking in target populations; longitudinal outcomes only with appropriate design.

## 8. Limitations

- No human plantar recordings in-repo (N_subjects real = 0).
- Simulator labels are not diabetic gait; zone labels are a function of gait class.
- Four FSRs cannot reconstruct shear or a full map; FSR nonlinearity and drift are not bench-quantified.
- Footwear, speed, and surface are not experimentally varied in hardware.
- No longitudinal ulcer outcomes.
- Image CNN excluded from the core paper; if trained later it remains unpaired.
- Battery unevaluated; BLE airtime unevaluated.
- Alert thresholds are engineering defaults (e.g. 75 kPa), not medically validated cut-offs.
- Bootstrap CIs on frozen table3/table4 used n_boot=80; last-mile scripts may recompute with 400.

These limitations are part of the scientific record.

## 9. Conclusion

X-Step specifies a four-site insole, a leakage-safe feature/ML stack, and simulator evidence about sparse sensing, robustness, and host latency. Claims remain proportional to that evidence. Physical calibration, field radio/power, and human walking data are required before any patient-facing performance statement.

## Acknowledgments / Conflict of interest

Removed for double-blind review.

## References

1. Armstrong DG, Boulton AJM, Bus SA (2017) Diabetic foot ulcers and their recurrence. N Engl J Med 376(24):2367–2375. https://doi.org/10.1056/NEJMra1615439
2. Bus SA, van Deursen RW, Armstrong DG, Lewis JEA, Caravaggi CF, Cavanagh PR (2016) Footwear and offloading interventions to prevent and heal foot ulcers and reduce plantar pressure in patients with diabetes: a systematic review. Diabetes Metab Res Rev 32(Suppl 1):99–118. https://doi.org/10.1002/dmrr.2702
3. Singh N, Armstrong DG, Lipsky BA (2005) Preventing foot ulcers in patients with diabetes. JAMA 293(2):217–228. https://doi.org/10.1001/jama.293.2.217
4. Hegde N, Bries M, Sazonov E (2016) A comparative review of footwear-based wearable systems. Electronics 5(3):48. https://doi.org/10.3390/electronics5030048
5. Abdul Razak AH, Zayegh A, Begg RK, Wahab Y (2012) Foot plantar pressure measurement system: a review. Sensors 12(7):9884–9912. https://doi.org/10.3390/s120709884
6. Fernando ME, Crowther RG, Pappas E, Lazzarini PA, Cunningham M, Sangla KS, Buttner P, Golledge J (2014) Plantar pressure in diabetic peripheral neuropathy patients with active foot ulceration, previous ulceration and no history of ulceration: a meta-analysis of observational studies. PLoS ONE 9(6):e99050. https://doi.org/10.1371/journal.pone.0099050
7. Schaper NC, van Netten JJ, Apelqvist J, Bus SA, Fitridge R, Game F, Monteiro-Soares M, Senneville E, on behalf of the IWGDF Editorial Board (2024) Practical guidelines on the prevention and management of diabetes-related foot disease (IWGDF 2023 update). Diabetes Metab Res Rev 40:e3657. https://doi.org/10.1002/dmrr.3657
8. Armstrong DG, Holtz-Neiderer K, Wendel C, Mohler MJ, Kimbriel HR, Lavery LA (2007) Skin temperature monitoring reduces the risk for diabetic foot ulceration in high-risk patients. Am J Med 120(12):1042–1046. https://doi.org/10.1016/j.amjmed.2007.06.028
9. Frykberg RG, Gordon IL, Reyzelman AM, et al. (2017) Feasibility and efficacy of a smart mat technology to predict development of diabetic plantar ulcers. Diabetes Care 40(7):973–980. https://doi.org/10.2337/dc16-2294
10. Lavery LA, Higgins KR, Lanctot DR, Constantinides GP, Zamorano RG, Athanasiou KA, Armstrong DG, Agrawal CM (2007) Preventing diabetic foot ulcer recurrence in high-risk patients: use of temperature monitoring as a self-assessment tool. Diabetes Care 30(1):14–20. https://doi.org/10.2337/dc06-1600
11. Cavanagh PR, Bus SA (2010) Off-loading the diabetic foot for ulcer prevention and healing. J Vasc Surg 52(3 Suppl):37S–43S. https://doi.org/10.1016/j.jvs.2010.06.007
12. Hegde N, Sazonov E (2014) SmartStep: a fully integrated, low-power insole monitor. Electronics 3(2):381–397. https://doi.org/10.3390/electronics3020381

Reference audit: `research/manuscript/reference_audit.csv`.
