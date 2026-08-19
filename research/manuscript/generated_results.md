# Results (generated from frozen tables)

These numbers are copied from CSV/JSON under `research/tables` and `research/results`. 
They are **not** typed by hand. **Data source for all quantitative ML rows below is `synthetic`** unless a row says otherwise. This is **not** patient generalization.

Cohort: **2592** windows, **24** virtual subjects, 25 Hz, 4 s windows, GroupKFold by subject unless specified.

## 6.1 Baseline models (subject-independent)

Logistic regression achieved macro-F1 **0.885** (bootstrap 95% CI 0.873–0.894) on grouped out-of-fold predictions; OOF AUROC 0.979. A majority-class dummy and a threshold heuristic are far lower. Small decimal gaps between logreg, hist-GBM, and MLP should not be interpreted as a meaningful ranking without overlapping-CI checks.

| model | accuracy | balanced_accuracy | macro_f1 | macro_f1_ci95_lo | macro_f1_ci95_hi | auroc_macro | serialized_kb | inference_mean_ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| threshold_heuristic | 0.49691358024691357 | 0.49535218601292363 | 0.47971451202685866 | 0.4598301677964287 | 0.4928722170094093 |  | 2.13 | 0.012765571591444314 |
| majority | 0.11072530864197531 | 0.1094282038004676 | 0.03998060677404628 | 0.03638163505766875 | 0.043299723005938005 |  |  |  |
| logreg | 0.8850308641975309 | 0.8846129873997054 | 0.8845971882742668 | 0.8729493692909518 | 0.8944384560951245 | 0.9789929687208301 | 7.74 | 0.06517509900731966 |
| decision_tree | 0.7854938271604939 | 0.7855784053740946 | 0.7957848540920687 | 0.7822201793608493 | 0.8116035618760957 |  | 11.64 | 0.04147290310356766 |
| linear_svm | 0.8738425925925926 | 0.8733552105382727 | 0.8727209306460951 | 0.8588449433437413 | 0.884084500133141 |  | 7.59 | 0.06790607294533402 |
| random_forest | 0.8344907407407407 | 0.8341878628609275 | 0.8369588576750404 | 0.8240827188025925 | 0.8506721156166585 |  | 3547.54 | 13.124740800412837 |
| gbm | 0.8695987654320988 | 0.8692023660113727 | 0.8701427304370215 | 0.8600894214697965 | 0.8810305902595795 |  |  |  |
| mlp | 0.8777006172839507 | 0.8771148449904188 | 0.8759779016212503 | 0.8637796477441485 | 0.8869177044745952 |  |  |  |
| hist_gbm | 0.8854166666666666 | 0.8850250893084906 | 0.8854802508199078 | 0.8746407541368676 | 0.8980149366535635 |  |  |  |

## 6.2 Split protocol (leakage check)

Random-window (IID) splitting can mix the same virtual subject across train and test. IID macro-F1 **0.931** vs subject-grouped **0.885** vs session-grouped **0.880**. If IID is substantially higher, the gap is treated as evidence of optimistic validation, not as a better model.

| protocol | macro_f1 | accuracy | macro_f1_ci95_lo | macro_f1_ci95_hi | note |
| --- | --- | --- | --- | --- | --- |
| iid_window | 0.9313491287297375 | 0.9301697530864198 | 0.9214393871548782 | 0.940965144094953 | random windows (subject leakage possible) |
| session | 0.8800112467831757 | 0.8784722222222222 | 0.8682857681051737 | 0.8917693515103706 | GroupKFold by session_id |
| subject | 0.8845971882742668 | 0.8850308641975309 | 0.8717336581907223 | 0.896062001690834 | GroupKFold by subject_id |
| loso | 0.8853910832306131 | 0.8854166666666666 | 0.8725227684568206 | 0.8969797290055198 | leave-one-subject-out |

## 6.3 Four-sensor ablation

The four-site configuration macro-F1 is **0.885**. Dropping MET5 yields **0.671**; dropping HEEL yields **0.657**. Single-site models remain near chance-to-weak. Four sensors are a **cost/information tradeoff on this simulator**, not a proof of clinical optimality.

| Sensor Configuration | Performance | delta_vs_4_sensor | Feature Count | Notes |
| --- | --- | --- | --- | --- |
| 4-site (met1+met2+met5+heel) | 0.8845729024622578 | 0.0 | 59 | 59 features still extracted; dropped sites are z |
| 3-site (met2+met5+heel) | 0.8829127034899618 | -0.0016601989722960786 | 59 | 59 features still extracted; dropped sites are z |
| 3-site (met1+met5+heel) | 0.8736789243547213 | -0.010893978107536562 | 59 | 59 features still extracted; dropped sites are z |
| 3-site (met1+met2+heel) | 0.6712263023881707 | -0.21334660007408712 | 59 | 59 features still extracted; dropped sites are z |
| 3-site (met1+met2+met5) | 0.656600395618381 | -0.22797250684387682 | 59 | 59 features still extracted; dropped sites are z |
| 2-site (met2+heel) | 0.6860149058469218 | -0.19855799661533602 | 59 | 59 features still extracted; dropped sites are z |
| 2-site (met1+heel) | 0.6638396516688048 | -0.22073325079345307 | 59 | 59 features still extracted; dropped sites are z |
| 2-site (met1+met2) | 0.43505059617871816 | -0.4495223062835397 | 59 | 59 features still extracted; dropped sites are z |
| 1-site (met2) | 0.3955332990198343 | -0.48903960344242353 | 59 | 59 features still extracted; dropped sites are z |
| 1-site (heel) | 0.42091694970667665 | -0.4636559527555812 | 59 | 59 features still extracted; dropped sites are z |
| 1-site (met1) | 0.39427538012774566 | -0.4902975223345122 | 59 | 59 features still extracted; dropped sites are z |
| 1-site (met5) | 0.3983056470732471 | -0.4862672553890107 | 59 | 59 features still extracted; dropped sites are z |
| 2-site (met1+met5) | 0.6391549956549898 | -0.24541790680726805 | 59 | 59 features still extracted; dropped sites are z |
| 2-site (met2+met5) | 0.6305626809468502 | -0.25401022151540764 | 59 | 59 features still extracted; dropped sites are z |
| 2-site (met5+heel) | 0.6491790269691249 | -0.23539387549313295 | 59 | 59 features still extracted; dropped sites are z |

## 6.4 Robustness

Under simulated BLE packet loss of 30%, held-out-subject macro-F1 is **0.631**. Degradation curves are reported in full; failure points are not hidden.

| perturbation | severity | macro_f1 | accuracy | data_source | validation_type |
| --- | --- | --- | --- | --- | --- |
| dropped_packets_frac | 0.0 | 0.8468313237746331 | 0.8487654320987654 | synthetic | engineering_simulation |
| dropped_packets_frac | 0.01 | 0.8391780862408954 | 0.8410493827160493 | synthetic | engineering_simulation |
| dropped_packets_frac | 0.05 | 0.8189109757893478 | 0.8209876543209876 | synthetic | engineering_simulation |
| dropped_packets_frac | 0.1 | 0.777847869335272 | 0.7824074074074074 | synthetic | engineering_simulation |
| dropped_packets_frac | 0.2 | 0.7141545528889707 | 0.720679012345679 | synthetic | engineering_simulation |
| dropped_packets_frac | 0.3 | 0.63050789633004 | 0.6450617283950617 | synthetic | engineering_simulation |

## 6.5 Sampling rate (no fake upsampling)

Training remains at 25 Hz. Testing on a 50% subsample (original samples only) yields macro-F1 **0.843**. BLE payload rate scales with sample rate (28 bytes × 2 feet × Hz).

| label | effective_hz | macro_f1 | ble_bytes_per_s_two_feet | note |
| --- | --- | --- | --- | --- |
| 100% (25 Hz) | 25.0 | 0.8468313237746331 | 1400.0 | train at 25 Hz; test uses original samples only  |
| 75% | 18.75 | 0.828558460108384 | 1050.0 | train at 25 Hz; test uses original samples only  |
| 50% (12.5 Hz) | 12.5 | 0.8431943171262201 | 700.0 | train at 25 Hz; test uses original samples only  |
| 25% (6.25 Hz) | 6.25 | 0.7144873409969522 | 350.0 | train at 25 Hz; test uses original samples only  |

## 6.6 Repeatability

Human test–retest ICC is **not reported** (no repeated walking sessions in-repo). Simulator within-session CV for `peak_any` (median) is **0.251**; between-seed ICC is **0.678**. These characterize the generator, not a person.

| feature | within_session_cv_median | within_session_mad_median | between_seed_icc | n_sessions | data_source | validation_type | note |
| --- | --- | --- | --- | --- | --- | --- | --- |
| peak_any | 0.25087557723026777 | 14.750634042717007 | 0.678430637166404 | 216 | synthetic | engineering_simulation | Simulator test-retest (seeds 67 vs 68), not huma |
| pti_total | 0.12919876127143395 | 33.88185524364137 | 0.4497011198783669 | 216 | synthetic | engineering_simulation | Simulator test-retest (seeds 67 vs 68), not huma |
| cadence_spm | 0.07515449391679957 | 8.333333333333334 | 0.7066422795835259 | 216 | synthetic | engineering_simulation | Simulator test-retest (seeds 67 vs 68), not huma |
| stance_ratio | 0.05295650052109949 | 0.03638888888888889 | 0.36994280405992414 | 216 | synthetic | engineering_simulation | Simulator test-retest (seeds 67 vs 68), not huma |
| forefoot_share | 0.02900412632840757 | 0.017554637781834928 | 0.6807712581354306 | 216 | synthetic | engineering_simulation | Simulator test-retest (seeds 67 vs 68), not huma |
| L_met1_peak | 0.13837567229192702 | 3.385378866334107 | 0.8667942210139115 | 216 | synthetic | engineering_simulation | Simulator test-retest (seeds 67 vs 68), not huma |
| L_met2_peak | 0.14289096171891036 | 3.8844172449114263 | 0.8068214983077637 | 216 | synthetic | engineering_simulation | Simulator test-retest (seeds 67 vs 68), not huma |
| L_met5_peak | 0.13401432676505898 | 2.7223002142323445 | 0.8889551099908197 | 216 | synthetic | engineering_simulation | Simulator test-retest (seeds 67 vs 68), not huma |
| L_heel_peak | 0.14450654342690678 | 4.328115353870425 | 0.7389409026968674 | 216 | synthetic | engineering_simulation | Simulator test-retest (seeds 67 vs 68), not huma |
| L_met2_load | 0.8765266810041654 | 0.033611111111111105 | 0.6453658494200571 | 216 | synthetic | engineering_simulation | Simulator test-retest (seeds 67 vs 68), not huma |
| HUMAN_REPEATABILITY |  |  |  | 0 | absent | not_run | No human repeated walking sessions in data/raw;  |

## 6.7 Sensor calibration vs ML accuracy

These quantities are not interchangeable. Simulated log–log reconstruction (not a bench measurement): MAE **1.3028493271009973** N, RMSE **2.019784450405351** N, MAPE **4.663059738959343** %. Physical load-cell residuals remain unmeasured.

## 6.8 Host latency (radio not measured)

Feature extraction mean **0.1565333644975908** ms; logreg mean **0.07454890903318301** ms; combined host path mean **0.23108227353077382** ms (P95 **0.3130475728539749**, P99 **0.5210357491159803**). Firmware sample period is 40 ms by design. BLE airtime is unmeasured.

## 6.9 Probability calibration

OOF ECE **0.03089637574820297**, Brier **0.18011262508706796**, AUROC **0.9789929687208301**. Platt scaling was fit on inner training groups only and is **not** adopted as the production calibrator (holdout Brier did not improve). Reliability diagrams use grouped OOF probabilities.

## 6.10 Thresholds

Peak-pressure cut-offs are **engineering risk-alert operating points** on synthetic non-normal vs normal labels, not medically validated ulcer thresholds.

| threshold_kpa | sensitivity | specificity | false_alert_rate | missed_event_rate | n_positive_true | label_definition | threshold_type | data_source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 40 | 0.8443866493281318 | 0.3157894736842105 | 0.6842105263157895 | 0.15561335067186824 | 2307 | synthetic gait class != normal (not a clinical u | engineering_risk_alert | synthetic |
| 55 | 0.6814044213263979 | 0.9333333333333333 | 0.06666666666666667 | 0.31859557867360205 | 2307 | synthetic gait class != normal (not a clinical u | engineering_risk_alert | synthetic |
| 75 | 0.4273948851322063 | 0.9859649122807017 | 0.014035087719298246 | 0.5726051148677936 | 2307 | synthetic gait class != normal (not a clinical u | engineering_risk_alert | synthetic |
| 100 | 0.19332466406588644 | 0.9894736842105263 | 0.010526315789473684 | 0.8066753359341136 | 2307 | synthetic gait class != normal (not a clinical u | engineering_risk_alert | synthetic |
| 125 | 0.06718682271348071 | 0.9964912280701754 | 0.0035087719298245615 | 0.9328131772865192 | 2307 | synthetic gait class != normal (not a clinical u | engineering_risk_alert | synthetic |
| 150 | 0.01907238838318162 | 1.0 | 0.0 | 0.9809276116168184 | 2307 | synthetic gait class != normal (not a clinical u | engineering_risk_alert | synthetic |
| 200 | 0.0017338534893801473 | 1.0 | 0.0 | 0.9982661465106198 | 2307 | synthetic gait class != normal (not a clinical u | engineering_risk_alert | synthetic |

## 6.11 Window duration (same-fs train/test)

| sample_hz | window_seconds | macro_f1 | note |
| --- | --- | --- | --- |
| 12.5 | 0.5 | 0.6995834551966129 | model trained and tested at the same fs/window;  |
| 12.5 | 1.0 | 0.7594719455997071 | model trained and tested at the same fs/window;  |
| 12.5 | 2.0 | 0.7982812450236049 | model trained and tested at the same fs/window;  |
| 12.5 | 5.0 | 0.834594428039129 | model trained and tested at the same fs/window;  |
| 25.0 | 0.5 | 0.775391335637725 | model trained and tested at the same fs/window;  |
| 25.0 | 1.0 | 0.7969275177557267 | model trained and tested at the same fs/window;  |
| 25.0 | 2.0 | 0.7567639421381068 | model trained and tested at the same fs/window;  |
| 25.0 | 5.0 | 0.8109215530718982 | model trained and tested at the same fs/window;  |
| 50.0 | 0.5 | 0.8223670171583812 | model trained and tested at the same fs/window;  |
| 50.0 | 1.0 | 0.6992963581915375 | model trained and tested at the same fs/window;  |
| 50.0 | 2.0 | 0.7483107504348909 | model trained and tested at the same fs/window;  |
| 50.0 | 5.0 | 0.5514574127576934 | model trained and tested at the same fs/window;  |


The frozen 4 s / 25 Hz window is a compromise between cadence estimates (need several steps) and alert latency. It is justified by this grid plus the 25 Hz firmware spec, not by clinical outcome data.
