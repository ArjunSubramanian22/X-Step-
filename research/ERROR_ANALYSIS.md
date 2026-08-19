# Error analysis

**Data source:** `synthetic` (not patient data unless labeled human).

Out-of-fold logistic regression misclassified **298 / 2592** windows.

## By class

| Class | N | Error rate |
| --- | --- | --- |
| normal | 285 | 0.312280701754386 |
| left_forefoot_overload | 291 | 0.06872852233676977 |
| right_forefoot_overload | 290 | 0.06551724137931035 |
| left_heel_overload | 288 | 0.0798611111111111 |
| right_heel_overload | 285 | 0.07368421052631578 |
| left_lateral_overload | 287 | 0.06620209059233449 |
| right_lateral_overload | 292 | 0.0958904109589041 |
| asymmetric_antalgic | 289 | 0.06228373702422145 |
| shuffling_low_cadence | 285 | 0.21403508771929824 |

## By peak-pressure tertile

Systematic weakness: if error rises in a tertile, the model is sensitive to amplitude rather than pattern.

| Bin | N | Error rate |
| --- | --- | --- |
| low_peak | 864 | 0.2337962962962963 |
| mid_peak | 864 | 0.07291666666666667 |
| high_peak | 864 | 0.03819444444444445 |

Participant-level error-rate mean (virtual subjects): 0.115 (SD 0.057).

Representative traces: `research/figures/fig_error_examples.*`.

Human walking speed / missing-packet / footwear slices are **not available** until `data_source=human`.
