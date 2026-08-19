# Claim-to-evidence matrix

Every important manuscript claim must map to an experiment. Evidence strength: **high** (measured on intended data), **moderate** (simulation/engineering), **none** (must not be claimed).

| Claim | Experiment | Figure/Table | Dataset | Evidence strength | Safe wording |
|-------|------------|--------------|---------|-------------------|--------------|
| Four FSR sites at MET1/MET2/MET5/HEEL stream at 25 Hz | Firmware + protocol tests | fig01, fig02, table1 | hardware contract | moderate (code/spec; not oscilloscope) | “Firmware is specified to sample four sites at 25 Hz” |
| 28-byte BLE v1 payload | `xstep_ml.protocol` tests | Methods | n/a | high (unit tests) | “Documented 28-byte little-endian frame” |
| Linear ADC→kPa is engineering default | `adc_to_kpa` | Methods | n/a | high as a software fact | “Not a fitted bench calibration” |
| Simulated calibration MAE/RMSE | `simulate_example_curve` | fig05, calibration_evaluation.json | simulated_example | none for the physical insole | “Pipeline demo on a known curve, not this device” |
| Logreg grouped macro-F1 ≈ 0.885 | GroupKFold subject OOF | table3 / model_comparison.csv, fig07 | synthetic 2592 windows | moderate (simulator) | “On the virtual cohort, grouped macro-F1 …” |
| Four-site vs fewer sites | Sensor ablation | table4 / sensor_ablation_publication.csv, fig08 | synthetic | moderate | “On these labels, dropping MET5 or heel reduces macro-F1 substantially” |
| Models compared fairly | Same splits, frozen HPs | model_comparison.csv | synthetic | moderate | “Under identical grouped CV and a priori HPs …” |
| IID can be optimistic | Split protocol comparison | split_protocol_comparison.csv | synthetic | moderate | “Random-window splits can mix subjects; grouped results are the ones we interpret” |
| Noise/packet-loss degrade performance | Perturbation holdout | fig09, fig10, packet_loss_sweep.csv | synthetic (simulated drops) | moderate as stress test | “Under simulated packet loss of X% …” |
| Host path is faster than 40 ms sample period | latency_host.json | fig11 | host CPU | moderate for host; none for radio | “Host feature+logreg latency; BLE airtime not measured” |
| 25 Hz can be reduced | sampling_rate_tradeoff.csv | fig13 | synthetic downsample | moderate | “Train at 25 Hz; test on original-sample subsets” |
| Repeatability quantified in humans | repeatability.csv | fig12 | absent human | **none** | “Not reported; no repeated walking sessions in-repo” |
| Battery runtime | power protocol | n/a | absent | **none** | Do not state hours of use |
| Prevents DFU / amputation | — | — | none | **none** | Forbidden |
| Diagnoses infection / ulcer | — | — | none | **none** | Forbidden |
| Clinically validated / FDA | — | — | none | **none** | Forbidden |
| Predicts ulcers | — | — | none | **none** | Forbidden for this device |
| Superior to Pedar/SmartMat | related_systems.csv | — | no head-to-head | **none** | “Different modality/complexity; no accuracy ranking” |
| LLM determines risk | STEPMATE_SAFETY.md | — | n/a | **none** (must not claim) | “Narration of deterministic factors only” |
| Ulcer CNN is a core result | supplementary | table7 | images gitignored | **none** for primary paper | “Out of scope” |

Risky-language scan: `python research/experiments/scan_claims.py` → `research/results/risky_language.csv` (manual review of each hit; reference titles may contain “prevent”).
