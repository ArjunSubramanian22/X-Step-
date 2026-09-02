# X-Step: Sparse Four-Site Plantar-Pressure Sensing for Continuous Risk Monitoring—Methods, Ablation, and Wearable Deployment Characterization

**Status:** EHB 2026 methods manuscript (double-blind). Quantitative Results are generated from `research/results/final_results_registry.json`. Do not paste unpublished decimals by hand.

**Validation type in this checkout:** Mixed. Gait/ML tables use a synthetic 4-FSR cohort. Four-site FSR force–ADC calibration is **operator-attested bench data** (`data/calibration/four_site_fsr_bench.csv`). Human walking in-repo is a **32-cell instrumented insole + OptiTrack** archive (15 adults, 149 analyzed takes), **not** X-Step four-site FSR402 recordings.

## Abstract

Repetitive plantar loading is a mechanical ingredient of diabetic foot ulcer (DFU) risk, yet dense pressure arrays are costly and often confined to the laboratory. Sparse, low-cost insoles can be worn outside the clinic, but it remains unclear how much biomechanical information four sites preserve, and whether classical models remain usable under wearable imperfections. We specify X-Step: four FSRs at the first, second, and fifth metatarsal heads and the heel (MET1, MET2, MET5, HEEL), sampled at 25 Hz on an ESP32 and streamed as a documented 28-byte Bluetooth Low Energy (BLE) payload, with a 59-dimensional feature set and a priori machine-learning (ML) baselines. All numerical ML results use a synthetic 24-subject, 2592-window cohort under subject-grouped cross-validation. Logistic regression achieved macro-F1 0.885 [95% CI: 0.873–0.894]. Within the evaluated layouts, dropping MET5 or HEEL reduced macro-F1 to 0.671 and 0.657, whereas dropping MET1 did not (0.883). Simulated 30% packet loss reduced held-out-subject macro-F1 from 0.847 to 0.631; host feature-plus-inference latency was 0.23 ms (P95 0.31 ms), below the 40 ms sample period. Operator-attested four-site FSR load–unload calibration reconstructed commanded force with MAE 1.69 N (RMSE 2.95 N). On a separate 15-adult overground archive recorded with a 32-cell insole (not the X-Step prototype), four anatomical sites tracked regional load time series (median *r* 0.717–0.986) and anteroposterior CoP (*r* 0.805). These results support an engineering feasibility case for sparse plantar monitoring. They do not establish clinical ulcer prediction, diagnostic replacement of a clinician, or reduction of limb-loss outcomes.

**Keywords:** plantar pressure; sparse sensing; wearable insole; gait feature; robustness; e-health

## 1. Introduction

Diabetic foot disease remains a major source of morbidity. IWGDF practical guidelines stratify clinical risk using neuropathy, peripheral artery disease, and ulcer history rather than a wearable classifier [7]. Mechanical load still matters: peak plantar pressure (PPP) and related quantities are established markers in observational syntheses [1–3,6], and offloading is central to ulcer care [2,11]. Clinic visits sample that load infrequently.

Plantar load monitoring is therefore an engineering target for unsupervised daily wear. Continuous in-shoe pressure can, in principle, characterize overload events, pressure-time integral (PTI), and gait features between visits. The scientific question is not whether a phone can display a heatmap, but whether a wearable sensor contract preserves enough information to support **biomechanical risk monitoring**.

Existing approaches occupy two poles. Dense capacitive or resistive arrays (Pedar-class, F-Scan-class) map the foot at high spatial resolution in gait laboratories [5]. Footwear wearables, including sparse FSR-plus-inertial systems such as SmartStep, demonstrate that fully embedded insoles are feasible, typically for activity or energy monitoring rather than four-site DFU-region pressure-risk characterization [4,12]. Home temperature tools have randomized evidence for a **different** modality [8–10]. A sparse pressure insole should not be ranked “more accurate” than those systems without a head-to-head experiment.

The sparse sensing problem is quantitative. If four sites are too few, ablation should show collapse. If three sites suffice for a given label set, the fourth sensor is optional complexity. If models only work on independent and identically distributed (IID) windows, they are not subject-independent. If they fail under noise, missing channels, or packet loss, they are not wearable. Host latency must be reported separately from radio airtime.

This paper investigates whether a sparse, low-cost four-site plantar-pressure architecture can preserve useful biomechanical information while supporting robust, real-time wearable **risk monitoring** under engineering evaluation. The mobile application is a recording client. An optional chat layer may only narrate already-computed factors. An unpaired ulcer-image convolutional network exists in the repository and is **not** part of this paper.

### Contributions

Each item maps to a Results subsection.

1. A documented four-site hardware and BLE contract (MET1, MET2, MET5, HEEL; 25 Hz; 28-byte payload) plus operator-attested FSR force–ADC calibration — Results §6.7–6.8 and Table I.
2. A reproducible 59-dimensional gait-feature pipeline with grouped splits and a priori classical ML — Results §6.1–6.2.
3. Sensor-ablation evidence for what the four sites contribute **within the evaluated configurations** — Results §6.3.
4. Robustness operating curves under noise, bias, missing channels, packet loss, and sampling-rate reduction — Results §6.4–6.5.
5. Host-side deployment characterization (model size, feature time, inference time) with radio and battery explicitly unmeasured — Results §6.8.
6. Sparse-versus-dense walking evidence on a 15-person 32-cell insole + OptiTrack archive, labeled as a different device from the four-site X-Step prototype — Results §6.12.

## 2. Related work

PPP and PTI are standard mechanical markers [2,6]. IWGDF 2023 practical guidelines do not endorse a four-FSR classifier as a diagnostic instrument [7]. Offloading remains central to prevention programs described in the clinical literature [2,11]; this paper does not evaluate those clinical programs.

Table `research/tables/related_systems.csv` compares study/system, year, modality, sensor count, population, real-time behavior, ML, robustness evaluation, deployment evaluation, and primary objective **only** using cited facts. We do not claim that X-Step is more accurate than Pedar-class arrays, SmartStep, or temperature trials. The intended gap is a **documented sparse pressure pipeline** with ablation, grouped ML, and robustness—not a new randomized trial.

DFU photographs are a separate literature. The optional public-image model is supplementary only.

## 3. System architecture

Each insole uses four FSR402-class sensors in 10 kΩ voltage dividers on ESP32 12-bit analog-to-digital converter (ADC) channels: MET1 GPIO34, MET2 GPIO35, MET5 GPIO32, HEEL GPIO33. Firmware (`firmware/xstep_insole/xstep_insole.ino`) samples at **25 Hz** (`delay(1000/SAMPLE_HZ)`) and notifies a 28-byte little-endian frame: magic `XS`, protocol version 1, side flags, sequence, boot-ms timestamp, four ADC samples, battery byte, reserved temperatures. GATT uses Nordic UART-style UUIDs. Two insoles (`XSTEP-L`, `XSTEP-R`) are fused on the host into shape \((T,8)\).

Engineering pressure uses a linear ADC→kPa map (250 kPa full scale after unloaded baseline). This is **not** a fitted bench curve. Research code can fit log–log force models when load-cell files exist (`xstep_ml.calibration`).

The mobile client historically labels the same four channels as toes / ball / arch / heel. Those strings are **UI aliases** of MET1 / MET2 / MET5 / HEEL; they are not additional anatomical sites.

Risk scores and alerts are deterministic (`xstep_ml.inference`). A language model must not set the score.

## 4. Methods

### 4.1 Hardware

- Sensors: four FSR402-class FSRs per insole.
- Sites: MET1 (first metatarsal head), MET2 (second metatarsal head), MET5 (fifth metatarsal head), HEEL (calcaneus). Placement is motivated by DFU spatial epidemiology [1,6], not by an optimization over a dense map in this study.
- Divider: 10 kΩ.
- Microcontroller: ESP32; ADC 12-bit (0–4095 counts).
- Sample rate: 25 Hz (40 ms loop) by firmware specification.
- Communication: BLE notify, 28-byte payload, protocol v1 (`xstep_ml/protocol.py`).
- Physical integration: research insole / development board; this paper does not report a commercial last or foam stack-up measurement.

### 4.2 Calibration

Unloaded baseline ADC is subtracted before the linear engineering map. This checkout includes `data/calibration/four_site_fsr_bench.csv`: 4 sites (MET1, MET2, MET5, HEEL), 5 load–unload trials, 12 commanded loads from 0–30 N (480 rows). The experimenter attests that these ADC–force pairs were physically measured; synthetic/generator stamps present in an earlier cleanup export were removed after that correction (`data/calibration/PROVENANCE.md`). Independent photographs and a load-cell serial number are **not** in the repository. This table is **not** a walking recording. Sensor calibration error is not classification accuracy. The firmware still uses a linear ADC→kPa engineering map unless a fitted curve is selected.

### 4.3 Data collection

- Human participants, X-Step four-site FSR walking: **none in this checkout** (\(N=0\)).
- Human walking, 32-cell insole + OptiTrack: **15** adults (7 female, 8 male; age 19–30, mean 23.4 years), **150** unique pressure takes, **149** analyzed after excluding P13 M1 (insole desynchronization per archive notes). M1–M10 labels are preserved as in the archive; they are not a coded speed protocol. Hardware is 32 pressure channels per foot (native counts 0–4096) plus OptiTrack Baseline Lower, **not** ESP32 FSR402 at 25 Hz. Pressure files have no timestamps; seconds and walking speed use a 64 Hz assumption from a sibling 32-channel schema [13]. Layout map: `research/data/insoles_optitrack/sensor_layout.json`. Evaluator: `python -m research.experiments.evaluate_insoles_optitrack`.
- Synthetic cohort: seed 67; 24 virtual subjects; 12 windows per gait class; 9 classes; 2592 windows; 4 s at 25 Hz; Gaussian noise SD 3.5 kPa; 3% label flips (`xstep_ml.data.synthetic_gait.make_cohort`). Dataset hash: `26180f5e5330adeac3088c43353bb05e83d90a120e2703ac673ec65e2781cd92`.
- Walking protocol for future X-Step 4-FSR recordings: `research/protocols/EHB26_WALKING_PROTOCOL.md`. Importer: `python -m research.import_real_data`.
- Footwear and exclusion rules for the 32-cell archive follow the operator zip (`info.txt`); ethics approval number is **not** in the files.

### 4.4 Signal processing

Windows are non-negative kPa arrays of shape \((T,8)\) with \(T=100\) at 25 Hz. Packet-loss fraction is computed from sequence gaps after import. Missing packets in robustness experiments are simulated by zeroing random time samples (not measured over the air). No stride-cut event detection is used in the frozen tables; segmentation is a **fixed 4 s window**.

### 4.5 Feature extraction

Production vectors have 59 named features (`xstep_ml.biomechanics.FEATURE_NAMES`). With window \(W\in\mathbb{R}^{T\times 8}\) and \(\Delta t=1/f_s\):

- Per-site PPP: \(\max_t p(t)\) (kPa).
- Per-site mean: \(\mathrm{mean}_t p(t)\) (kPa).
- Per-site PTI: \(\sum_t p(t)\,\Delta t\) (kPa·s).
- Loaded-contact fraction: \(\mathrm{mean}_t \mathbf{1}[p>30~\mathrm{kPa}]\).
- High-PPP occupancy: fraction above 200 kPa (literature high-PPP band, not a device claim).
- Asymmetry, cadence (steps/min), stance ratio, anterior pressure share, `peak_any`, `pti_total`.

The default alert cut-off \(\tau_{\mathrm{alert}}=75\) kPa is an **engineering risk-alert threshold**, not a medically validated ulcer threshold. Extended definitions: `research/METHODS_FEATURES.md`.

### 4.6 Machine learning

Algorithms (a priori, `research/configs/HYPERPARAMETERS.md`, `random_state=67`): threshold heuristic; majority dummy; logistic regression (production gait head: `StandardScaler` + `LogisticRegression(max_iter=400, class_weight="balanced")`); decision tree; linear SVM; random forest; gradient boosting; MLP; histogram gradient boosting. No test-set hyperparameter search. Zone labels in the simulator are **derived from gait class**.

### 4.7 Data splitting

Primary protocol: 5-fold GroupKFold by `subject_id`. Additional protocols: GroupKFold by `session_id`; leave-one-subject-out; IID StratifiedKFold as an **optimistic** control. Split dumps: `research/results/splits/`. Leakage tests fail if subject or session IDs overlap across a forbidden partition. StandardScaler lives **inside** the sklearn Pipeline and is fit on training folds only.

### 4.8 Statistics

Primary metric: macro-F1. Secondary: accuracy, balanced accuracy, AUROC when probabilities exist, Brier score, expected calibration error (ECE). Uncertainty: percentile bootstrap 95% confidence intervals (CIs). Frozen table generation used `n_boot=80` in the original experiment manifest; later OOF scripts may recompute CIs with 400 resamples. **Canonical CIs for logistic regression in this paper are those in `model_comparison.csv`.** Effect sizes are absolute Δmacro-F1 (IID−subject; drop-MET5; drop-HEEL). McNemar tests are exploratory and not used as a ranking device. SAP: `research/STATISTICAL_ANALYSIS_PLAN.md`.

### 4.9 System benchmarking

Host latency: 200 repeats of feature extraction and logistic-regression inference on a 4 s window (`research/results/latency_host.json`). Firmware sample period is 40 ms **by specification**, not an oscilloscope measurement. BLE airtime, packet error rate on the air, memory on the ESP32 beyond the 28-byte notify, and battery life are **not measured**. Power protocol: `research/protocols/POWER_MEASUREMENT_PROTOCOL.md`.

## 5. Experiments

Frozen configuration: `research/releases/EHB26_EXPERIMENTAL_FREEZE.md`. Training (`make experiments`) is separate from paper build (`make paper`). The paper pipeline **does not retrain**.

## 6. Results

All ML numbers are **synthetic**. Canonical rounded values follow `final_results_registry.json`. Full tables: `research/manuscript/generated_results.md`. Human 32-cell walking numbers in §6.12 are **not** gait-classifier scores.

**Figure 1.** System architecture: four FSR sites, ESP32 ADC at 25 Hz, 28-byte BLE `XS` payload, host features, deterministic engineering alerts, and a mobile recorder. Synthetic/engineering context; not a patient study. (`fig01_architecture`)

**Figure 2.** Canonical plantar sites MET1, MET2, MET5, and HEEL. App strings toes/ball/arch/heel are aliases of these four sites only. (`fig02_plantar_layout`)

**Figure 3.** Processing pipeline from raw ADC to windowed features, model or threshold, and alert. (`fig03_pipeline`)

**Figure 4.** Representative simulated left-foot pressure traces (kPa vs time) for one overload pattern. Illustrative of the generator, not a recorded volunteer. (`fig04_gait_cycle`)

### 6.1 Baseline models (subject-independent)

Logistic regression achieved macro-F1 **0.885 [95% CI: 0.873–0.894]** on grouped out-of-fold (OOF) predictions (accuracy 0.885; OOF AUROC 0.979; ECE 0.031). Histogram gradient boosting was 0.885 [0.875–0.898]. A majority dummy was 0.040; a threshold heuristic was 0.480. Linear SVM was 0.873. Random forest was 0.837 with a 3.5 MB artifact versus 7.7 kB for logistic regression. Overlapping CIs among the strongest linear and boosting models are **not** interpreted as a ranking.

**Figure 5.** Model comparison under subject-grouped cross-validation. Bars: macro-F1; error bars: bootstrap 95% CI. Dataset: synthetic 2592 windows / 24 virtual subjects. (`fig07_model_comparison`)

**Figure 6.** Grouped-CV confusion matrix for logistic regression (same cohort). (`fig06_confusion`)

### 6.2 Split protocol (leakage check)

IID-window splitting yielded macro-F1 **0.931** versus **0.885** subject-grouped and **0.880** session-grouped (Δ IID−subject = 0.047). Leave-one-subject-out was 0.885. The IID gap is treated as optimistic validation, not as the paper result.

### 6.3 Four-sensor ablation

Within the evaluated configurations, four-site macro-F1 was **0.885**. Going from one site (MET2: 0.396) to two mixed sites is inconsistent: MET1+MET2 is 0.435, whereas MET2+HEEL is 0.686. Three-site subsets that retain MET5 and HEEL stay near four-site performance (drop MET1: 0.883, Δ −0.002). Dropping MET5 yields **0.671** (Δ −0.213); dropping HEEL yields **0.657** (Δ −0.228). Single-site models remain 0.39–0.42. We do **not** claim the four-site arrangement is globally optimal.

**Figure 7.** Sensor-site ablation for logistic regression (subject-grouped CV) with bootstrap 95% CI. Dropped channels are zeroed; the feature vector length remains 59. (`fig08_sensor_ablation`)

Peak-only features (9-D) reached 0.886 versus 0.885 for the full 59-D set, indicating that **on this simulator** the gait labels are largely peak-separable. That fact is a high-performance caveat, not a clinical virtue.

### 6.4 Robustness

Robustness uses a **grouped 25% subject holdout** with a clean-training baseline macro-F1 of **0.847**—a different estimand from 5-fold OOF 0.885. Table V reports relative change versus that holdout baseline.

| Perturbation | Severity | Baseline | Perturbed | Relative change |
| --- | --- | --- | --- | --- |
| Gaussian noise | 12 kPa SD | 0.847 | 0.641 | −0.243 |
| Packet loss | 30% | 0.847 | 0.631 | −0.255 |
| Missing channel | HEEL=0 | 0.847 | 0.218 | −0.742 |
| Sensor bias | +15 kPa | 0.847 | 0.181 | −0.787 |
| Sampling keep | 50% (12.5 Hz) | 0.847 | 0.843 | −0.004 |

Operational reading: moderate packet loss is damaging but graded; a dead heel or fifth-metatarsal channel, or a large constant bias, is a **failure mode**. Mild noise at 1.5–3.5 kPa did not reduce holdout F1 relative to the noisy simulator already used in training; 12 kPa SD did. Packet loss is **simulated** by zeroing samples.

**Figure 8.** Noise and packet-loss operating curves (held-out subjects). (`fig09_robustness_noise`, `fig10_packet_loss`)

### 6.5 Sampling rate

Training remains at 25 Hz. Testing on original samples only: 75% keep 0.829; 50% keep 0.843; 25% keep (6.25 Hz) 0.714. Theoretical two-foot BLE payload rate scales as \(28\times 2\times f_s\) bytes/s (1400 bytes/s at 25 Hz). Field radio occupancy is unmeasured.

### 6.6 Repeatability

X-Step four-site human test–retest ICC is **not reported**. Simulator `peak_any` median CV and between-seed ICC characterize the generator only (`repeatability.csv`). The 32-cell archive’s M1–M10 takes are unlabeled movement identifiers, not repeated identical walking trials, so they are not used as test–retest ICC.

### 6.7 Sensor calibration versus ML accuracy

Four-site log–log reconstruction on the operator-attested bench CSV (480 rows, `data_source=bench`): pooled MAE **1.69 N**, RMSE **2.95 N**, MAPE **14.4%** on commanded force > 0.25 N, mean loading–unloading hysteresis **2.02 N**. Per-site MAE: MET1 1.44 N, MET2 1.65 N, MET5 1.52 N, HEEL 2.16 N (`research/tables/calibration_four_site.csv`). These residuals are ADC→force curve error, not gait macro-F1, and are not walking-trial accuracy.

**Figure 9.** Commanded force (N) versus ADC counts at MET1, MET2, MET5, and HEEL for five load–unload trials. Loading and unloading are shown separately. Dataset: operator-attested `four_site_fsr_bench.csv` (not a walking study). (`fig05_calibration`)

### 6.8 Host latency and deployment

Feature extraction mean 0.16 ms; logistic regression 0.07 ms; combined host path mean **0.23 ms** (P95 **0.31 ms**, P99 0.52 ms); \(n=200\) host repeats. Firmware sample period is 40 ms by design. Serialized logistic regression is **7.7 kB** (540 parameters). BLE radio notify time is **not measured**. Battery life is **not measured** and is not estimated here.

**Figure 10.** Host-side latency for features, logistic regression, and the combined path. Whiskers: P95. Radio excluded. (`fig11_latency`)

### 6.9 Probability calibration

OOF ECE 0.031, Brier 0.180, AUROC 0.979. Platt scaling on inner training groups is **not** adopted (holdout Brier did not improve).

### 6.12 Human 32-cell walking (not the X-Step prototype)

Fifteen healthy adults (7 female, 8 male; age 19–30 years) walked with a 32-cell instrumented insole synchronized to OptiTrack. This is **not** a recording of the four-site FSR402 X-Step insole. After excluding one desynchronized take (P13 M1), **149** takes remain (298 foot-takes). Pressure CSVs have no timestamps; a 64 Hz assumption yields median take duration 4.6 s, median pelvis path 5.68 m, and median speed **1.23 m/s**.

Four a priori anatomical cells (MET1, MET2, MET5, HEEL analogs; separate left/right maps from `insoles-number.jpeg`) were compared with the regional maximum of the dense array. Median time-series Pearson *r* (single cell vs region-max): MET1 **0.879**, MET2 **0.986**, MET5 **0.717**, HEEL **0.885**. Peak-to-peak *r* is lower (0.429–0.739), as expected when one cell under-samples a cluster. Four-site CoP reconstructed from unit-foot coordinates tracked native anteroposterior CoP (median *r* **0.805**) and did **not** recover mediolateral CoP (*r* 0.005). Heel loading preceded mean forefoot loading on 69% of foot-takes. Native units are insole counts (0–4096), not X-Step kPa. Frozen synthetic macro-F1 tables were not retrained on these takes.

**Figure 11.** Single-site peak versus dense regional-max peak for MET1, MET2, MET5, and HEEL analogs. 15 adults, 32-cell insole, overground walking; not X-Step FSR402. (`fig14_human_sparse_vs_dense`)

**Figure 12.** Example left-foot four-site subsample (P1 M1) in native counts versus time at the assumed 64 Hz. (`fig15_human_walking_traces`)

## 7. Discussion

**Evidence levels.** Level A is physical engineering evidence (sensor operation, bench calibration, BLE on the air, measured latency, packet loss, repeatability). This paper contributes Level A **specifications, host-CPU latency, operator-attested four-site FSR force–ADC calibration, and a 32-cell overground walking archive used only as sparse-versus-dense evidence**. It does **not** contribute measured radio, battery, or X-Step four-site FSR walking. Independent lab photographs of the calibration rig are not in the repository. Level B is algorithmic evidence (classification, ablation, robustness, grouped validation) on the stated dataset—here, a **synthetic** cohort. Level C is clinical evidence (future ulcer occurrence, prevented events, decision impact, patient outcomes). **Level A or B results are not Level C.** Grouped macro-F1 0.885 is Level B on a simulator. Four-site versus 32-cell correlations are Level A/B on a **different** insole.

**Why four sensors?** Within the evaluated configurations, MET5 and HEEL carry the overload-pattern labels; MET1 is nearly redundant with the other three on this generator. Four sites are a reasonable cost/information tradeoff **for these labels**, not a clinical standard.

**Does it generalize?** Subject-grouped CV is the headline protocol for the simulator. The 15 walking adults wore a 32-cell insole, not X-Step. There are no unseen X-Step four-site FSR participants.

**Is it robust?** Failure is explicit: missing heel, +15 kPa bias, 30% simulated loss. That is an operational requirement for donning, sweat, and radio, not a claim of field reliability.

**Is it deployable?** Host inference is fast relative to 40 ms. Wearable deployment still requires measured BLE and power.

**Novelty.** Prior dense systems maximize spatial maps [5]. Prior sparse wearables often target activity [12]. Temperature RCTs target a different signal [8–10]. X-Step’s supported combination is: clinically motivated four-site contract + quantitative ablation + grouped ML + wearable-like perturbations + host latency + a reproducible repository. We do not claim that no prior sparse insole exists.

## 8. Limitations

- No X-Step four-site FSR walking recordings (\(N=0\)). The human walking archive is a 32-cell insole + OptiTrack dataset; it does not validate ESP32 FSR402 ADC, 25 Hz `XS` packets, or the linear kPa map.
- Pressure timestamps are absent; 64 Hz and 1.23 m/s are assumption-dependent.
- M1–M10 are unlabeled takes, not a coded slow/normal/fast protocol.
- Four anatomical cells under-sample regional peaks (peak-to-peak *r* 0.43–0.74); mediolateral CoP is not recovered.
- Simulator labels are not diabetic gait; zone labels are a function of gait class.
- Four FSRs cannot reconstruct shear or a full pressure map; FSR nonlinearity and drift are not bench-quantified.
- AUROC 0.979 and grouped F1 0.885 are plausible because the generator is largely peak-separable (peak-only ≈ full features); they are **not** patient performance.
- No longitudinal ulcer outcomes (Level C absent).
- Image CNN excluded from the core paper.
- Battery unevaluated; BLE airtime unevaluated.
- Alert thresholds are engineering defaults.
- Ethics approval number is not in the walking archive.
- Bootstrap \(n\) differs between the original freeze (`n_boot=80`) and some later OOF scripts; canonical intervals are `model_comparison.csv`.

These limitations are part of the scientific record.

## 9. Conclusion

X-Step specifies a four-site insole, operator-attested FSR force–ADC calibration, a leakage-aware feature/ML stack, and simulator evidence about sparse sensing, robustness, and host latency. A 15-adult 32-cell walking archive shows that four anatomical sites can track regional load and anteroposterior CoP on a dense insole; that is not a field validation of the FSR402 prototype. Claims remain proportional to that mix of Level A measurements and Level B synthetic experiments. Field radio, power, and X-Step four-site walking data are required before any patient-facing performance statement.

## Data availability

All ML tables in this checkout were produced from the in-repository synthetic generator (`make_cohort`, seed 67). Four-site FSR force–ADC pairs are in `data/calibration/four_site_fsr_bench.csv` as operator-attested bench measurements (provenance in `data/calibration/PROVENANCE.md`). Human walking traces used here are the operator-provided `InsolesOpitrackDataset` archive (SHA-256 `6f11afbb50c555738ead3be7051218c1e79ecd29ed8ac53e404e8f770133561a`); the file layout matches Zenodo 10.5281/zenodo.20156243 [13]. Derived summaries are in `research/results/human_optitrack_evaluation.json`. The 84 MB zip is not stored in git. Scripts: `python -m research.import_real_data` (X-Step 4-FSR sessions) and `python -m research.experiments.evaluate_insoles_optitrack`.

## Code availability

Source: https://github.com/ArjunSubramanian22/X-Step- (branch `ehb26-research`). Reproducibility: `make test` and `make paper` (the latter does not retrain). License: MIT (`LICENSE`). Experimental freeze tag `v0.9-ehb26-experimental` must not be moved; submission freeze uses a separate release-candidate tag.

## Ethics

No IRB or ethics approval number appears in this repository or in the walking zip. The 32-cell archive uses pseudonymous codes P1–P15 and aggregate demographics only. Prospective X-Step four-site walking studies require institutional review and consent before they are conducted; wording must be confirmed by the team (`research/HUMAN_VERIFICATION_REQUIRED.md`).

## Author contributions

CRediT roles cannot be inferred from git history alone. Placeholders requiring team confirmation are listed in `research/HUMAN_VERIFICATION_REQUIRED.md`.

## Acknowledgments / Conflict of interest

Removed for double-blind review. Funding, patents, and conflicts require human confirmation.

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
13. Multimodal gait dataset: synchronized sensorized-insole (pressure + IMU) and OptiTrack motion capture recordings (2026) Zenodo. https://doi.org/10.5281/zenodo.20156243

Reference audit: `research/manuscript/reference_audit.csv`.
