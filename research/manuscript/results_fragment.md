**Data source:** `synthetic`  
**Validation type:** `engineering_simulation`  
**Windows / subjects:** 2592 / 24  
**Dataset hash:** `26180f5e5330adea…`

## Table 3. Model comparison (auto-generated)

| model | data_source | validation_type | split | accuracy | balanced_accuracy | precision_macro | recall_macro | specificity_macro | macro_f1 | weighted_f1 | macro_f1_ci95_lo | macro_f1_ci95_hi | auroc_macro | pr_auc_macro | brier | ece | fold_macro_f1_mean | fold_macro_f1_std | n_windows | n_subjects |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| threshold_heuristic | synthetic | engineering_simulation | GroupKFold-subject | 0.49691358024691357 | 0.49535218601292363 | 0.6123139387181337 | 0.49535218601292363 | 0.937116565266085 | 0.47971451202685866 | 0.48086920481331463 | 0.4598301677964287 | 0.4928722170094093 |  |  |  |  | 0.4749842666309584 | 0.03703560490547116 | 2592 | 24 |
| majority | synthetic | engineering_simulation | GroupKFold-subject | 0.11072530864197531 | 0.1094282038004676 | 0.024588477366255145 | 0.1094282038004676 | 0.8886755600904458 | 0.03998060677404628 | 0.04046399634605799 | 0.03638163505766875 | 0.043299723005938005 |  |  |  |  | 0.0221554442589501 | 0.00013355592654424182 | 2592 | 24 |
| logreg | synthetic | engineering_simulation | GroupKFold-subject | 0.8850308641975309 | 0.8846129873997054 | 0.8847408644622891 | 0.8846129873997054 | 0.9856357648412598 | 0.8845971882742668 | 0.8850328478733365 | 0.8729493692909518 | 0.8944384560951245 |  |  |  |  | 0.8852705676125632 | 0.01475559343574575 | 2592 | 24 |
| decision_tree | synthetic | engineering_simulation | GroupKFold-subject | 0.7854938271604939 | 0.7855784053740946 | 0.8222086507516178 | 0.7855784053740946 | 0.9732012322020888 | 0.7957848540920687 | 0.7960161610727922 | 0.7822201793608493 | 0.8116035618760957 |  |  |  |  | 0.7963349141594097 | 0.043155664528529016 | 2592 | 24 |
| linear_svm | synthetic | engineering_simulation | GroupKFold-subject | 0.8738425925925926 | 0.8733552105382727 | 0.8725388730735235 | 0.8733552105382727 | 0.9842382777049399 | 0.8727209306460951 | 0.8732314100379334 | 0.8588449433437413 | 0.884084500133141 |  |  |  |  | 0.8739551981464733 | 0.012725189676779197 | 2592 | 24 |
| random_forest | synthetic | engineering_simulation | GroupKFold-subject | 0.8344907407407407 | 0.8341878628609275 | 0.8429364811055066 | 0.8341878628609275 | 0.9793212320872132 | 0.8369588576750404 | 0.8373889420286821 | 0.8240827188025925 | 0.8506721156166585 |  |  |  |  | 0.8412475483596802 | 0.028477115225793506 | 2592 | 24 |
| gbm | synthetic | engineering_simulation | GroupKFold-subject | 0.8695987654320988 | 0.8692023660113727 | 0.871730404174689 | 0.8692023660113727 | 0.983707817504519 | 0.8701427304370215 | 0.870587453911354 | 0.8600894214697965 | 0.8810305902595795 |  |  |  |  | 0.8707045758307954 | 0.021711729048152953 | 2592 | 24 |
| mlp | synthetic | engineering_simulation | GroupKFold-subject | 0.8777006172839507 | 0.8771148449904188 | 0.8756636593614292 | 0.8771148449904188 | 0.9847172643284084 | 0.8759779016212503 | 0.8764545658027932 | 0.8637796477441485 | 0.8869177044745952 |  |  |  |  | 0.8755882956327621 | 0.015217873375370125 | 2592 | 24 |
| hist_gbm | synthetic | engineering_simulation | GroupKFold-subject | 0.8854166666666666 | 0.8850250893084906 | 0.8863116900834758 | 0.8850250893084906 | 0.9856848278323209 | 0.8854802508199078 | 0.8859210673802059 | 0.8746407541368676 | 0.8980149366535635 |  |  |  |  | 0.8853848387487989 | 0.025462370003090366 | 2592 | 24 |

## Table 4. Sensor ablation

| subset | label | n_sites | macro_f1 | macro_f1_ci95_lo | macro_f1_ci95_hi | fold_macro_f1_mean | data_source | validation_type |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 4_all | 4-site (met1+met2+met5+heel) | 4 | 0.8845729024622578 | 0.8729493692909518 | 0.8944384560951245 | 0.8852705676125632 | synthetic | engineering_simulation |
| 3_no_met1 | 3-site (met2+met5+heel) | 3 | 0.8829127034899618 | 0.8732048140156919 | 0.8935868114761069 | 0.8848375138752598 | synthetic | engineering_simulation |
| 3_no_met2 | 3-site (met1+met5+heel) | 3 | 0.8736789243547213 | 0.8638372415380101 | 0.8845200297311488 | 0.8762732997235141 | synthetic | engineering_simulation |
| 3_no_met5 | 3-site (met1+met2+heel) | 3 | 0.6712263023881707 | 0.6518235044690921 | 0.6876927115327843 | 0.6698131019408551 | synthetic | engineering_simulation |
| 3_no_heel | 3-site (met1+met2+met5) | 3 | 0.656600395618381 | 0.6418423963946578 | 0.670650788682025 | 0.6527035754321917 | synthetic | engineering_simulation |
| 2_met2_heel | 2-site (met2+heel) | 2 | 0.6860149058469218 | 0.6714302492631767 | 0.6999751920660807 | 0.682917072083036 | synthetic | engineering_simulation |
| 2_met1_heel | 2-site (met1+heel) | 2 | 0.6638396516688048 | 0.6484555809782551 | 0.6775921001712866 | 0.6647941935617431 | synthetic | engineering_simulation |
| 2_met1_met2 | 2-site (met1+met2) | 2 | 0.43505059617871816 | 0.4202235110318594 | 0.4473234814810056 | 0.42914611167009953 | synthetic | engineering_simulation |
| 1_met2 | 1-site (met2) | 1 | 0.3955332990198343 | 0.3819614114582228 | 0.407336876337717 | 0.3953869937659694 | synthetic | engineering_simulation |
| 1_heel | 1-site (heel) | 1 | 0.42091694970667665 | 0.4101225906031086 | 0.4381271586227681 | 0.41326686894914266 | synthetic | engineering_simulation |
| 1_met1 | 1-site (met1) | 1 | 0.39427538012774566 | 0.38040052303771305 | 0.41011683269799754 | 0.3936329486507634 | synthetic | engineering_simulation |
| 1_met5 | 1-site (met5) | 1 | 0.3983056470732471 | 0.3868510862550798 | 0.4112417862834951 | 0.3982937297452751 | synthetic | engineering_simulation |

## Table 5. Robustness (excerpt in CSV)

| perturbation | severity | macro_f1 | accuracy | data_source | validation_type |
| --- | --- | --- | --- | --- | --- |
| none | 0.0 | 0.8468313237746331 | 0.8487654320987654 | synthetic | engineering_simulation |
| gaussian_noise_kpa | 1.5 | 0.8812803368076231 | 0.8827160493827161 | synthetic | engineering_simulation |
| gaussian_noise_kpa | 3.5 | 0.8804789576471382 | 0.8827160493827161 | synthetic | engineering_simulation |
| gaussian_noise_kpa | 7.0 | 0.827634511150332 | 0.8317901234567902 | synthetic | engineering_simulation |
| gaussian_noise_kpa | 12.0 | 0.6411388665764197 | 0.6697530864197531 | synthetic | engineering_simulation |
| calibration_drift_gain | 0.05 | 0.8405829895026402 | 0.8425925925925926 | synthetic | engineering_simulation |
| calibration_drift_gain | 0.15 | 0.8408222718152664 | 0.8425925925925926 | synthetic | engineering_simulation |
| calibration_drift_gain | 0.3 | 0.8234112369619422 | 0.8271604938271605 | synthetic | engineering_simulation |
| dropped_packets_frac | 0.02 | 0.8403580213198611 | 0.8425925925925926 | synthetic | engineering_simulation |
| dropped_packets_frac | 0.08 | 0.806157875731929 | 0.808641975308642 | synthetic | engineering_simulation |
| dropped_packets_frac | 0.2 | 0.7076148866130682 | 0.7160493827160493 | synthetic | engineering_simulation |
| missing_sensor_index | 0.0 | 0.5051548259694791 | 0.5370370370370371 | synthetic | engineering_simulation |
| missing_sensor_index | 1.0 | 0.29325689325689325 | 0.3595679012345679 | synthetic | engineering_simulation |
| missing_sensor_index | 2.0 | 0.3808031559950973 | 0.4521604938271605 | synthetic | engineering_simulation |
| missing_sensor_index | 3.0 | 0.2181655755460958 | 0.3271604938271605 | synthetic | engineering_simulation |
| short_dropout_samples | 2.0 | 0.836795714026001 | 0.8395061728395061 | synthetic | engineering_simulation |
| short_dropout_samples | 5.0 | 0.8177777987026124 | 0.8209876543209876 | synthetic | engineering_simulation |
| short_dropout_samples | 12.0 | 0.8067679266510585 | 0.8101851851851852 | synthetic | engineering_simulation |
| sensor_bias_kpa | 5.0 | 0.7611714352002994 | 0.7484567901234568 | synthetic | engineering_simulation |
| sensor_bias_kpa | 15.0 | 0.18050941794838404 | 0.2222222222222222 | synthetic | engineering_simulation |
| sensor_bias_kpa | 30.0 | 0.054016362252663624 | 0.1419753086419753 | synthetic | engineering_simulation |
| sampling_rate_factor | 1.0 | 0.8468313237746331 | 0.8487654320987654 | synthetic | engineering_simulation |
| sampling_rate_factor | 2.0 | 0.8755250257389933 | 0.875 | synthetic | engineering_simulation |
| sampling_rate_factor | 4.0 | 0.7766564579174521 | 0.7731481481481481 | synthetic | engineering_simulation |
| timing_jitter_frac | 0.0 | 0.8468313237746331 | 0.8487654320987654 | synthetic | engineering_simulation |
| timing_jitter_frac | 0.15 | 0.8706576468100339 | 0.8719135802469136 | synthetic | engineering_simulation |
| timing_jitter_frac | 0.35 | 0.8739924181749892 | 0.875 | synthetic | engineering_simulation |

## Table 6. System performance

| Stage | Mean Latency | Median | P95 | Std Dev | Notes |
| --- | --- | --- | --- | --- | --- |
| BLE packet decode (host, not radio) | 0.0019126266124658287 | 0.0015409896150231361 | 0.001710085780359804 | 0.004399882535926626 | Software decode of 28-byte payload. Radio/airtime not measured in this repo. |
| Preprocessing / feature extraction | 0.16271863132715225 | 0.15050001093186438 | 0.24895896203815926 | 0.04259980672249096 | 4.0s window at 25.0 Hz, host CPU. |
| Inference (logreg_production) | 0.07351037784246728 | 0.06141650374047458 | 0.0712211040081456 | 0.06810378149423309 | serialized 7.74 KB; params=540 |
| Inference (zone_gbm) | 0.33824999554781243 | 0.32245798502117395 | 0.42393681651446957 | 0.04328331990640685 | serialized 722.74 KB; params=0 |
| Inference (threshold_heuristic) | 0.012816593516618013 | 0.012603995855897665 | 0.013551473966799676 | 0.0009607102007753982 | serialized 2.13 KB; params=None |
| Inference (logreg) | 0.06207275437191129 | 0.06143751670606434 | 0.06663955864496529 | 0.002819439783207154 | serialized 7.74 KB; params=540 |
| Inference (decision_tree) | 0.04726452461909503 | 0.04308350617066026 | 0.07910025597084311 | 0.015551483107576456 | serialized 11.64 KB; params=None |
| Inference (linear_svm) | 0.07988224679138511 | 0.06104150088503957 | 0.08308543474413443 | 0.10018914321853403 | serialized 7.59 KB; params=540 |
| Inference (random_forest) | 12.576419772813097 | 12.607666983967647 | 12.92033604113385 | 0.28375086537896926 | serialized 3547.54 KB; params=0 |
| FSR sample period (firmware design) | 40.0 | 40.0 | 40.0 |  | 25 Hz design specification from firmware delay; not a scope measurement. |
| BLE radio notify (not measured) |  |  |  |  | Requires instrumented ESP32 + phone capture. Do not invent values. |
| Host alert path (features + one model) | 2.047035240684636 |  | 2.200083345607189 |  | Excludes BLE airtime and UI render. Engineering host timing only. |
