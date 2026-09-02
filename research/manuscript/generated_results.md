# Results (generated from final_results_registry.json)

All quantitative ML rows below are **synthetic / engineering validation** unless a cell says otherwise. 
Display rounding: rates to 3 decimals; latency to 0.01 ms; force to 0.01 N. 
Registry git SHA at build: `87d6164d56dc4c075c6fbd4a33fb2e03addc4821`. Dataset hash: `26180f5e5330adeac3088c43353bb05e83d90a120e2703ac673ec65e2781cd92`.

Cohort: **2592** windows, **24** virtual subjects, **0** X-Step four-site FSR walking subjects, **15** adults in the 32-cell insole+OptiTrack archive (not the X-Step prototype), 25 Hz synthetic windows.

## 6.1 Baseline models (subject-independent)

Logistic regression achieved macro-F1 **0.885 [95% CI: 0.873–0.894]** on grouped out-of-fold predictions (OOF AUROC 0.979; ECE 0.031). A majority dummy was 0.040 and a threshold heuristic was 0.480. Histogram gradient boosting was 0.885; overlapping CIs mean this is not a ranking.

| model | macro_f1 | macro_f1_ci95_lo | macro_f1_ci95_hi | accuracy | auroc_macro | ece | serialized_kb | inference_mean_ms | data_source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| threshold_heuristic | 0.480 | 0.460 | 0.493 | 0.497 |  |  | 2.130 | 0.013 | synthetic |
| majority | 0.040 | 0.036 | 0.043 | 0.111 |  |  |  |  | synthetic |
| logreg | 0.885 | 0.873 | 0.894 | 0.885 | 0.979 | 0.031 | 7.740 | 0.065 | synthetic |
| decision_tree | 0.796 | 0.782 | 0.812 | 0.785 |  |  | 11.640 | 0.041 | synthetic |
| linear_svm | 0.873 | 0.859 | 0.884 | 0.874 |  |  | 7.590 | 0.068 | synthetic |
| random_forest | 0.837 | 0.824 | 0.851 | 0.834 |  |  | 3547.540 | 13.125 | synthetic |
| gbm | 0.870 | 0.860 | 0.881 | 0.870 |  |  |  |  | synthetic |
| mlp | 0.876 | 0.864 | 0.887 | 0.878 |  |  |  |  | synthetic |
| hist_gbm | 0.885 | 0.875 | 0.898 | 0.885 |  |  |  |  | synthetic |

## 6.2 Split protocol (leakage check)

IID-window macro-F1 **0.931** vs subject-grouped **0.885 [95% CI: 0.873–0.894]** vs session-grouped **0.880** (Δ IID−subject = 0.047). IID is an optimistic control, not the paper result.

| protocol | macro_f1 | accuracy | macro_f1_ci95_lo | macro_f1_ci95_hi | note |
| --- | --- | --- | --- | --- | --- |
| iid_window | 0.931 | 0.930 | 0.921 | 0.941 | random windows (subject leakage possible) |
| session | 0.880 | 0.878 | 0.868 | 0.892 | GroupKFold by session_id |
| subject | 0.885 | 0.885 | 0.872 | 0.896 | GroupKFold by subject_id |
| loso | 0.885 | 0.885 | 0.873 | 0.897 | leave-one-subject-out |

## 6.3 Four-sensor ablation

Within the evaluated configurations, four-site macro-F1 is **0.885**. Dropping MET5 yields **0.671** (Δ -0.213); dropping HEEL yields **0.657** (Δ -0.228); dropping MET1 yields **0.883**. One-site MET2 is **0.396**. Four sensors are a cost/information tradeoff on this simulator, not a globally optimal layout.

| Sensor Configuration | Performance | delta_vs_4_sensor | n_sites | macro_f1_ci95_lo | macro_f1_ci95_hi | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| 4-site (met1+met2+met5+heel) | 0.885 | 0.000 | 4 | 0.873 | 0.894 | 59 features still extracted; dropped sites are zeroed. S |
| 3-site (met2+met5+heel) | 0.883 | -0.002 | 3 | 0.873 | 0.894 | 59 features still extracted; dropped sites are zeroed. S |
| 3-site (met1+met5+heel) | 0.874 | -0.011 | 3 | 0.864 | 0.885 | 59 features still extracted; dropped sites are zeroed. S |
| 3-site (met1+met2+heel) | 0.671 | -0.213 | 3 | 0.652 | 0.688 | 59 features still extracted; dropped sites are zeroed. S |
| 3-site (met1+met2+met5) | 0.657 | -0.228 | 3 | 0.642 | 0.671 | 59 features still extracted; dropped sites are zeroed. S |
| 2-site (met2+heel) | 0.686 | -0.199 | 2 | 0.671 | 0.700 | 59 features still extracted; dropped sites are zeroed. S |
| 2-site (met1+heel) | 0.664 | -0.221 | 2 | 0.648 | 0.678 | 59 features still extracted; dropped sites are zeroed. S |
| 2-site (met1+met2) | 0.435 | -0.450 | 2 | 0.420 | 0.447 | 59 features still extracted; dropped sites are zeroed. S |
| 1-site (met2) | 0.396 | -0.489 | 1 | 0.382 | 0.407 | 59 features still extracted; dropped sites are zeroed. S |
| 1-site (heel) | 0.421 | -0.464 | 1 | 0.410 | 0.438 | 59 features still extracted; dropped sites are zeroed. S |
| 1-site (met1) | 0.394 | -0.490 | 1 | 0.380 | 0.410 | 59 features still extracted; dropped sites are zeroed. S |
| 1-site (met5) | 0.398 | -0.486 | 1 | 0.387 | 0.411 | 59 features still extracted; dropped sites are zeroed. S |
| 2-site (met1+met5) | 0.639 | -0.245 | 2 | 0.624 | 0.653 | 59 features still extracted; dropped sites are zeroed. S |
| 2-site (met2+met5) | 0.631 | -0.254 | 2 | 0.615 | 0.644 | 59 features still extracted; dropped sites are zeroed. S |
| 2-site (met5+heel) | 0.649 | -0.235 | 2 | 0.635 | 0.663 | 59 features still extracted; dropped sites are zeroed. S |

## 6.4 Robustness

Held-out-subject baseline macro-F1 is **0.847** (a different estimand from 5-fold OOF). Simulated 30% packet loss: **0.631**. Gaussian noise SD 12 kPa: **0.641**. Missing heel channel: **0.218**. Constant +15 kPa bias: **0.181**.

| perturbation | severity | baseline_macro_f1 | perturbed_macro_f1 | relative_change | source | data_source |
| --- | --- | --- | --- | --- | --- | --- |
| none | 0 | 0.847 | 0.847 | 0.000 | table5_robustness.csv | synthetic |
| gaussian_noise_kpa | 12 | 0.847 | 0.641 | -0.243 | table5_robustness.csv | synthetic |
| dropped_packets_frac | 0.30 | 0.847 | 0.631 | -0.255 | packet_loss_sweep.csv | synthetic |
| missing_channel_heel | heel=0 | 0.847 | 0.218 | -0.742 | table5_robustness.csv | synthetic |
| sensor_bias_kpa | 15 | 0.847 | 0.181 | -0.787 | table5_robustness.csv | synthetic |
| sampling_keep_frac | 0.50 | 0.847 | 0.843 | -0.004 | sampling_rate_tradeoff.csv | synthetic |

## 6.5 Sampling rate (no fake upsampling)

Training remains at 25 Hz. Testing on a 50% subsample (original samples only) yields macro-F1 **0.843**.

| label | effective_hz | macro_f1 | ble_bytes_per_s_two_feet | note |
| --- | --- | --- | --- | --- |
| 100% (25 Hz) | 25.000 | 0.847 | 1400.000 | train at 25 Hz; test uses original samples only (no upsa |
| 75% | 18.750 | 0.829 | 1050.000 | train at 25 Hz; test uses original samples only (no upsa |
| 50% (12.5 Hz) | 12.500 | 0.843 | 700.000 | train at 25 Hz; test uses original samples only (no upsa |
| 25% (6.25 Hz) | 6.250 | 0.714 | 350.000 | train at 25 Hz; test uses original samples only (no upsa |

## 6.6 Repeatability

X-Step four-site test–retest ICC is **not reported** (no repeated 4-FSR walking sessions). Simulator CVs characterize the generator only. M1–M10 in the 32-cell archive are unlabeled takes, not identical repeats.

| feature | within_session_cv_median | within_session_mad_median | between_seed_icc | n_sessions | data_source | validation_type | note |
| --- | --- | --- | --- | --- | --- | --- | --- |
| peak_any | 0.251 | 14.750634042717007 | 0.678 | 216 | synthetic | engineering_simulation | Simulator test-retest (seeds 67 vs 68), not human ICC |
| pti_total | 0.129 | 33.88185524364137 | 0.450 | 216 | synthetic | engineering_simulation | Simulator test-retest (seeds 67 vs 68), not human ICC |
| cadence_spm | 0.075 | 8.333333333333334 | 0.707 | 216 | synthetic | engineering_simulation | Simulator test-retest (seeds 67 vs 68), not human ICC |
| stance_ratio | 0.053 | 0.03638888888888889 | 0.370 | 216 | synthetic | engineering_simulation | Simulator test-retest (seeds 67 vs 68), not human ICC |
| forefoot_share | 0.029 | 0.017554637781834928 | 0.681 | 216 | synthetic | engineering_simulation | Simulator test-retest (seeds 67 vs 68), not human ICC |
| L_met1_peak | 0.138 | 3.385378866334107 | 0.867 | 216 | synthetic | engineering_simulation | Simulator test-retest (seeds 67 vs 68), not human ICC |
| L_met2_peak | 0.143 | 3.8844172449114263 | 0.807 | 216 | synthetic | engineering_simulation | Simulator test-retest (seeds 67 vs 68), not human ICC |
| L_met5_peak | 0.134 | 2.7223002142323445 | 0.889 | 216 | synthetic | engineering_simulation | Simulator test-retest (seeds 67 vs 68), not human ICC |
| L_heel_peak | 0.145 | 4.328115353870425 | 0.739 | 216 | synthetic | engineering_simulation | Simulator test-retest (seeds 67 vs 68), not human ICC |
| L_met2_load | 0.877 | 0.033611111111111105 | 0.645 | 216 | synthetic | engineering_simulation | Simulator test-retest (seeds 67 vs 68), not human ICC |
| HUMAN_REPEATABILITY |  |  |  | 0 | absent | not_run | No human repeated walking sessions in data/raw; values n |

## 6.7 Sensor calibration vs ML accuracy

These quantities are not interchangeable. Four-site log–log reconstruction on operator-attested `data/calibration/four_site_fsr_bench.csv` (480 load–unload rows; not walking data): MAE **1.69 N**, RMSE **2.95 N**. Lab photographs of the rig are not in the repository.

## 6.8 Host latency (radio not measured)

Combined host path mean **0.23 ms** (P95 **0.31 ms**). Firmware sample period is 40 ms by design. BLE airtime is unmeasured. Serialized logreg size **7.7 kB**.

| quantity | value | source |
| --- | --- | --- |
| Serialized logistic regression | 7.7 kB | model_comparison.csv |
| Feature extraction mean | 0.23 ms path; see latency_host.json | latency_host.json |
| Host path mean (features + logreg) | 0.23 ms | latency_host.json |
| Host path P95 | 0.31 ms | latency_host.json |
| Firmware sample period | 40 ms | firmware SAMPLE_HZ=25 |
| BLE radio airtime | not measured | n/a |
| Battery life | not measured (future work) | POWER_MEASUREMENT_PROTOCOL.md |

## 6.9 Probability calibration

OOF ECE **0.031**, AUROC **0.979**. Platt scaling was fit on inner training groups only and is **not** adopted as the production calibrator.

## 6.10 Thresholds

Peak-pressure cut-offs are **engineering risk-alert operating points** on synthetic non-normal vs normal labels, not medically validated ulcer thresholds.

| threshold_kpa | sensitivity | specificity | false_alert_rate | missed_event_rate | n_positive_true | label_definition | threshold_type | data_source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 40.000 | 0.844 | 0.316 | 0.684 | 0.156 | 2307 | synthetic gait class != normal (not a clinical ulcer eve | engineering_risk_alert | synthetic |
| 55.000 | 0.681 | 0.933 | 0.067 | 0.319 | 2307 | synthetic gait class != normal (not a clinical ulcer eve | engineering_risk_alert | synthetic |
| 75.000 | 0.427 | 0.986 | 0.014 | 0.573 | 2307 | synthetic gait class != normal (not a clinical ulcer eve | engineering_risk_alert | synthetic |
| 100.000 | 0.193 | 0.989 | 0.011 | 0.807 | 2307 | synthetic gait class != normal (not a clinical ulcer eve | engineering_risk_alert | synthetic |
| 125.000 | 0.067 | 0.996 | 0.004 | 0.933 | 2307 | synthetic gait class != normal (not a clinical ulcer eve | engineering_risk_alert | synthetic |
| 150.000 | 0.019 | 1.000 | 0.000 | 0.981 | 2307 | synthetic gait class != normal (not a clinical ulcer eve | engineering_risk_alert | synthetic |
| 200.000 | 0.002 | 1.000 | 0.000 | 0.998 | 2307 | synthetic gait class != normal (not a clinical ulcer eve | engineering_risk_alert | synthetic |

## 6.11 Window duration (same-fs train/test)

| sample_hz | window_seconds | n_samples | macro_f1 | fold_macro_f1_mean | data_source | validation_type | note |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 12.500 | 0.500 | 6 | 0.700 | 0.7112680111049302 | synthetic | engineering_simulation | model trained and tested at the same fs/window; not a de |
| 12.500 | 1.000 | 12 | 0.759 | 0.7561114837166416 | synthetic | engineering_simulation | model trained and tested at the same fs/window; not a de |
| 12.500 | 2.000 | 25 | 0.798 | 0.7842287098003684 | synthetic | engineering_simulation | model trained and tested at the same fs/window; not a de |
| 12.500 | 5.000 | 62 | 0.835 | 0.8299215453324226 | synthetic | engineering_simulation | model trained and tested at the same fs/window; not a de |
| 25.000 | 0.500 | 12 | 0.775 | 0.7791158587137791 | synthetic | engineering_simulation | model trained and tested at the same fs/window; not a de |
| 25.000 | 1.000 | 25 | 0.797 | 0.7898973105535226 | synthetic | engineering_simulation | model trained and tested at the same fs/window; not a de |
| 25.000 | 2.000 | 50 | 0.757 | 0.7208677783183101 | synthetic | engineering_simulation | model trained and tested at the same fs/window; not a de |
| 25.000 | 5.000 | 125 | 0.811 | 0.7949973914103984 | synthetic | engineering_simulation | model trained and tested at the same fs/window; not a de |
| 50.000 | 0.500 | 25 | 0.822 | 0.821072119821172 | synthetic | engineering_simulation | model trained and tested at the same fs/window; not a de |
| 50.000 | 1.000 | 50 | 0.699 | 0.6658332000453394 | synthetic | engineering_simulation | model trained and tested at the same fs/window; not a de |
| 50.000 | 2.000 | 100 | 0.748 | 0.7338572792919952 | synthetic | engineering_simulation | model trained and tested at the same fs/window; not a de |
| 50.000 | 5.000 | 250 | 0.551 | 0.550004448150303 | synthetic | engineering_simulation | model trained and tested at the same fs/window; not a de |


The frozen 4 s / 25 Hz window is a compromise between cadence estimates and alert latency.

## 6.12 Human 32-cell walking (not X-Step FSR)

**15** adults, **149** analyzed takes (150 unique pressure takes, one excluded for insole desynchronization). Hardware is a 32-cell instrumented insole synchronized to OptiTrack, **not** the four-site FSR402 prototype. Median anteroposterior CoP correlation (4 anatomical sites vs native 32-cell CoP): **0.805**. Mediolateral CoP is not recovered (**0.005**). Single-site vs regional-max time-series *r*: MET1 0.879, MET2 0.986, MET5 0.717, HEEL 0.885. Median overground speed **1.23 m/s** under a 64 Hz timestamp assumption. These numbers are not mixed into the frozen synthetic gait macro-F1 tables.

| site | n_foot_takes | median_timeseries_r | peak_peak_r | peak_rmse_counts | peak_nrmse | median_sparse_peak | median_dense_peak | data_source | hardware |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| met1 | 298.000 | 0.879 | 0.429 | 1146.4259 | 0.446 | 1852.5000 | 2635.5000 | human | 32-cell insole, not X-Step 4-FSR |
| met2 | 298.000 | 0.986 | 0.529 | 647.0099 | 0.269 | 1950.5000 | 2432.0000 | human | 32-cell insole, not X-Step 4-FSR |
| met5 | 298.000 | 0.717 | 0.554 | 1056.7326 | 0.375 | 2034.0000 | 2834.0000 | human | 32-cell insole, not X-Step 4-FSR |
| heel | 298.000 | 0.885 | 0.739 | 566.5793 | 0.181 | 2800.5000 | 3191.0000 | human | 32-cell insole, not X-Step 4-FSR |

