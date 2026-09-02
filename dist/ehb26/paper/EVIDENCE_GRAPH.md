# Evidence graph

Every major quantitative or scientific statement in the manuscript must have this chain:

`Claim → Dataset → Experiment → Result file → Figure/Table → Manuscript section`

Unsupported claims are marked **UNSUPPORTED** and must not appear in the paper.

| Claim | Dataset | Experiment | Result file | Figure/Table | Section |
| --- | --- | --- | --- | --- | --- |
| Four FSR sites MET1/MET2/MET5/HEEL at 25 Hz | hardware contract | firmware spec | `firmware/xstep_insole/xstep_insole.ino` | Table I, Fig. 1–2 | §3, §4.1, §6.8 |
| 28-byte BLE v1 payload | n/a | protocol unit tests | `xstep_ml/protocol.py` | Table I | §3, §4.1 |
| Linear ADC→kPa, 250 kPa FS, not bench | n/a | `adc_to_kpa` | `xstep_ml/hardware.py` | Table I | §3, §4.2 |
| Four-site operator-attested FSR calibration MAE 1.69 N, RMSE 2.95 N | `four_site_fsr_bench` (480 rows, `data_source=bench`) | log–log reconstruction | `research/results/calibration_evaluation.json` | Fig. 9, Table calibration_four_site | §4.2, §6.7 |
| 24 virtual subjects, 2592 windows, seed 67 | `synthetic_4fsr_gait` | `make_cohort` | `research/results/manifest.json` | Table II | §4.3, §6 |
| Human walking, X-Step 4-FSR \(N=0\) | `human_walking_fsr` | data inventory | `research/data_inventory.json` | Table II | §4.3, §8 |
| 15 adults, 149 32-cell takes, not X-Step FSR | `human_32site_insole_optitrack` | sparse vs dense | `research/results/human_optitrack_evaluation.json` | Fig. 11–12, Table human_optitrack | §4.3, §6.12 |
| 4-site vs dense AP CoP *r* 0.805 | same | 4-site CoP vs native copY | same JSON | Fig. 11 | §6.12 |
| Logreg grouped macro-F1 0.885 [0.873–0.894] | synthetic | GroupKFold-subject OOF | `research/tables/model_comparison.csv` | Fig. 5, Table III | §6.1 |
| OOF AUROC 0.979, ECE 0.031 | synthetic | grouped OOF probabilities | `research/results/probability_calibration.json` | §6.9 | §6.1, §6.9 |
| Heuristic 0.480; majority 0.040 | synthetic | same CV | `model_comparison.csv` | Fig. 5 | §6.1 |
| IID 0.931 vs subject 0.885 (Δ 0.047) | synthetic | split protocol | `split_protocol_comparison.csv` | §6.2 | §6.2 |
| Four-site F1 0.885; drop MET5 0.671; drop HEEL 0.657; drop MET1 0.883 | synthetic | sensor ablation | `sensor_ablation_publication.csv` | Fig. 7, Table IV | §6.3 |
| 1-site MET2 0.396 | synthetic | sensor ablation | same | Table IV | §6.3 |
| Peak-only F1 0.886 ≈ full 0.885 | synthetic | feature ablation | `feature_ablation.csv` | supplement | §6.3, HIGH_PERFORMANCE_AUDIT |
| Holdout baseline F1 0.847 | synthetic | grouped 25% holdout | `table5_robustness.csv` | Table V | §6.4 |
| Packet loss 30% → 0.631 | synthetic | packet sweep | `packet_loss_sweep.csv` | Fig. 8 | §6.4 |
| Noise 12 kPa SD → 0.641 | synthetic | robustness | `table5_robustness.csv` | Fig. 8 | §6.4 |
| Missing HEEL → 0.218 | synthetic | missing_sensor index 3 | `table5_robustness.csv` | Table V | §6.4 |
| Bias +15 kPa → 0.181 | synthetic | sensor_bias | `table5_robustness.csv` | Table V | §6.4 |
| Sampling 50% keep → 0.843 | synthetic | downsample original samples | `sampling_rate_tradeoff.csv` | §6.5 | §6.5 |
| Host path 0.23 ms (P95 0.31 ms) | host CPU | latency repeats \(n=200\) | `latency_host.json` | Fig. 9, Table VI | §6.8 |
| Logreg 7.7 kB / 540 params | synthetic artifact | efficiency | `model_comparison.csv` | Table VI | §6.8 |
| BLE airtime | — | — | — | — | **UNSUPPORTED** (stated unmeasured) |
| Battery life | — | — | — | — | **UNSUPPORTED** (future work) |
| Human ICC / repeatability | — | — | `repeatability.csv` empty of X-Step humans | — | **UNSUPPORTED** as 4-FSR test–retest |
| Four sites globally optimal | — | ablation is not a global search | — | — | **UNSUPPORTED** (rewritten as “within evaluated configurations”) |
| Predicts / detects ulcers | — | — | — | — | **UNSUPPORTED** |
| Prevents DFU or limb loss | — | — | — | — | **UNSUPPORTED** |
| Superior to Pedar / SmartMat | — | no head-to-head | `related_systems.csv` | Table related work | **UNSUPPORTED** |
| FDA / hospital / clinically proven | — | — | — | — | **UNSUPPORTED** |
| LLM sets risk | — | STEPMATE policy | `research/STEPMATE_SAFETY.md` | — | **UNSUPPORTED** (forbidden) |
| Ulcer CNN core result | public images gitignored | not in freeze | `table7_ulcer.csv` | supplement | **UNSUPPORTED** for primary paper |
