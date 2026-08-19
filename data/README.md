# Data

No raw private patient data, credentials, or identifiable telemetry belong in this repository.

## Layout

```
data/README.md                 this file
data/calibration/TEMPLATE.csv  empty bench schema
data/calibration/SIMULATED_example.csv  generated, labeled SIMULATED
data/examples/                 optional tiny synthetic CSV (no PHI)
```

## Canonical schema

`xstep_ml.data.schema.PressureSample` / `PressureWindowRecord`

Sites: `met1`, `met2`, `met5`, `heel`. App aliases: toes→met1, ball→met2, arch→met5, heel→heel.

## Sources

| Name | Provenance | Commit? |
| --- | --- | --- |
| Synthetic gait windows | Generator | generated at runtime |
| Simulated calibration curve | Known log-log + noise | yes, labeled simulated |
| Human walking | Future | **never** commit identifiable files |
| DFU photos | Public archive | gitignored |

When human data exist, store them outside git (or git-lfs with access control) and point `CohortBundle.data_source = "human"`.
