# Consistency audit

Source of truth: frozen CSVs/JSON under `research/tables` and `research/results`, then `final_results_registry.json`. When two files disagree, **the experiment file wins**, not the more flattering prose.

| Topic | Conflict found | Resolution | Evidence |
| --- | --- | --- | --- |
| Paper title | README used “A Low-Cost Four-Site Smart Insole…”; manuscript used “Sparse Four-Site…” | Canonical title is the manuscript sparse-sensing title | `research/manuscript/main.md` |
| CITATION.cff | Title said “diabetic foot ulcer **prevention**” | Rewritten to risk monitoring; prevention is Level C and unsupported | this audit + `CITATION.cff` |
| Production model | Artifact `gait_pattern_rf.joblib` vs logistic regression | Describe as logreg; filename is historical | `models/MODEL_CARD.md` |
| Sample rate | Firmware 25 Hz vs any 50 Hz illustrative plot | Methods/results: 25 Hz. Fig. 4 may use a short illustrative generator call; caption must say simulated traces | `SAMPLE_HZ = 25`; `latency` 40 ms |
| Sensor names | App toes/ball/arch vs MET1/MET2/MET5/HEEL | Paper uses MET*; aliases mentioned once | `xstep_ml/hardware.py` |
| Subject count | 24 virtual; 0 X-Step 4-FSR humans; 15 adults on a 32-cell insole | Stated in Table II, abstract, §6.12 | `manifest.json`, `data_inventory.json`, `human_optitrack_evaluation.json` |
| Logreg F1 | `model_comparison.csv` 0.8846 vs split-protocol subject 0.8846 vs ablation 4_all 0.8846 | Canonical **0.885 [0.873–0.894]** from `model_comparison.csv` | slight CI differences from separate bootstraps; split-protocol subject CI 0.872–0.896 is **not** used in the abstract |
| n_boot | Freeze config 80 vs some last-mile scripts 400 | Canonical CIs = CSV next to the metric | `manifest.json` `n_boot=80` |
| Packet-loss grid | `table5` used 2/8/20%; `packet_loss_sweep.csv` uses 0/1/5/10/20/30% | Paper uses `packet_loss_sweep.csv` | 30% → 0.631 |
| Robustness baseline | OOF 0.885 vs holdout 0.847 | Both reported; Table V uses holdout 0.847 | different estimands |
| Sampling 2×/4× in table5 | Interpolation factors exist in old robustness table | Paper **does not** use those as evidence of higher fs; uses `sampling_rate_tradeoff.csv` (original samples only) | §6.5 |
| Host alert path | `table6` “Host alert path” ~2.05 ms vs `latency_host.json` 0.23 ms | Canonical host path = `latency_host.json` (features+logreg). table6 mixed zone GBM / older path | `latency_host.json` |
| Model card path | `docs/MODEL_CARD.md` pointed at `papers/ehb2026/tables/ehb_results.json` | Point to `research/tables/model_comparison.csv` | this audit |
| Calibration MAE | Old single-site demo 1.30 N vs four-site bench 1.69 N | Canonical calibration section uses `calibration_evaluation.json` from `four_site_fsr_bench.csv` (1.69 N / 2.95 N). Operator-attested bench; not walking. | `calibration_evaluation.json` |
| Ulcer table | table7 exists | Explicitly out of primary paper | `SUPPLEMENTARY_ULCER.md` |
| README current results | pointed at table3 / results_fragment | Point to registry + generated_results | `README.md` |
| Hist-GBM vs logreg | 0.8855 vs 0.8846 | Tie within CI; no “best model” claim | `model_comparison.csv` |

## Numbers that must not reappear as headlines

- IID 0.931 as “accuracy of X-Step”
- Any 99% toy accuracy
- Battery hours
- BLE milliseconds on the air
- Patient \(N>0\) on the **X-Step four-site FSR** (still zero)
- Treating the 32-cell OptiTrack archive as FSR402 walking
