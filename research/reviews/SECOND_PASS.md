# Simulated review — second pass (after last-mile fixes)

Fixes that were actually implemented (no new physical data):

| Concern | Fix |
|---------|-----|
| IID leakage | `split_protocol_comparison.csv` + dumped split JSON |
| Missing AUROC/ECE | logreg OOF `predict_proba` |
| Packet loss only 2/8/20% | sweep 1/5/10/20/30% |
| Host latency averaged RF | logreg-only host path + P99 |
| Ulcer CNN in core paper | supplementary only |
| Fernando 2015 / wrong article | 2014 PLoS ONE e99050 |
| IWGDF 2019 authors | 2023 board (Schaper … Senneville) |
| LLM as contribution | StepMate = narration only |
| No importer | `python -m research.import_real_data` |
| Calibration vs ML mixed | `calibration_evaluation.json` + manuscript §6.7 |
| Extra 2-site subsets | MET1+MET5, MET2+MET5, MET5+HEEL |
| Repeatability fabricated | pipeline only; human row empty |

**Unfixed (require a lab / people):** bench FSR curve, BLE airtime, battery, human walking N, clinical outcomes.

Re-scores after text/code fixes, **same evidence**: R1 5, R2 7, R3 4 (clinical) / 7 (methods), R4 5.5, R5 5.5. Mean ≈ **5.6 / 10**. Still not camera-ready as a human-subjects wearable paper.
