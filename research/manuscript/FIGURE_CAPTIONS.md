# Figure captions (standalone)

Use these captions in the Springer template. Every caption states the dataset/condition.

**Figure 1. System architecture.** Four force-sensitive resistors at MET1, MET2, MET5, and HEEL are sampled at 25 Hz on an ESP32 and notified as a 28-byte BLE `XS` payload. The host computes biomechanical features and a deterministic engineering risk-alert. The mobile app records; it does not define risk. Engineering/specification diagram, not a patient study.

**Figure 2. Plantar sensor sites.** Canonical hardware locations: first metatarsal (MET1), second metatarsal (MET2), fifth metatarsal (MET5), heel (HEEL). Mobile strings toes/ball/arch/heel are aliases of these four sites only.

**Figure 3. Signal-processing pipeline.** Raw ADC → engineering kPa map → 4 s window → 59 features → model or threshold → alert and record.

**Figure 4. Representative plantar-pressure traces.** Simulated left-foot pressure (kPa) versus time (s) for one overload pattern from the synthetic generator. Not a recorded volunteer.

**Figure 5. Model comparison.** Macro-F1 under 5-fold GroupKFold by virtual subject. Error bars: percentile bootstrap 95% CI. Dataset: synthetic 2592 windows, 24 virtual subjects, `data_source=synthetic`.

**Figure 6. Confusion matrix.** Out-of-fold logistic-regression predictions, same grouped protocol and synthetic cohort as Figure 5.

**Figure 7. Sensor ablation.** Logistic-regression macro-F1 when selected sites are zeroed (feature dimension remains 59). Error bars: bootstrap 95% CI. Within the evaluated configurations only; not a global layout optimum.

**Figure 8. Robustness.** Left: Gaussian measurement noise (kPa SD). Right: simulated packet loss (% of time samples zeroed). Metric: macro-F1 on held-out virtual subjects after training on clean windows. Not over-the-air BLE measurements.

**Figure 9. Four-site FSR force–ADC calibration.** Commanded force (N) versus ADC counts at MET1, MET2, MET5, and HEEL. Five operator-attested load–unload trials (`data/calibration/four_site_fsr_bench.csv`). Not a walking study.

**Figure 10. Host latency.** Mean feature extraction, logistic-regression inference, and combined host path (ms). Whiskers: 95th percentile. BLE radio time excluded. Firmware sample period is 40 ms by specification.

**Figure 11. Four anatomical sites versus dense regional peaks.** Single-cell peak (counts) versus the maximum of the same anatomical cluster on a 32-cell insole. Fifteen adults, overground walking. Not the X-Step four-site FSR402 prototype. Native counts 0–4096.

**Figure 12. Example four-site subsample.** Left-foot MET1/MET2/MET5/HEEL analog traces from one take (P1 M1). Time axis uses the 64 Hz assumption (no timestamps in the CSV). Not X-Step kPa.
