# Clinical / claim-language audit

Classification of phrases searched in the manuscript and repo docs.

| Phrase | Occurrences (intent) | Class | Action |
| --- | --- | --- | --- |
| detect ulcers / detects ulcers | none as a device claim | unsupported if used | not in `main.md` |
| predict ulcers | Frykberg **title** of a temperature mat RCT [9] | supported as citation of **that** study, not X-Step | kept in References only |
| prevent ulcers / prevents | literature titles [3,10,11]; X-Step does not claim this | unsupported for X-Step | paper uses “do not establish … reduction of limb-loss outcomes” |
| prevent amputations | none | unsupported | omitted |
| diagnose / diagnosis | avoided as a whole word in `main.md` | unsupported for X-Step | “diagnostic replacement of a clinician” denied |
| infection detection | none | unsupported | omitted |
| clinical accuracy | none | unsupported | omitted |
| medically validated / clinically proven | none positive | unsupported | omitted |
| superior / state-of-the-art / proven / guarantees | none positive | unsupported | omitted |
| validated in patients / hospital validated | none | unsupported | omitted |
| FDA | not in `main.md` | unsupported as clearance | `docs/ETHICS.md` states not cleared |
| high grouped macro-F1 | measured 0.885 | **supported** as Level B synthetic | kept with CI and dataset label |
| real-time | host path 0.23 ms vs 40 ms spec | **partial** (host only) | radio excluded |
| four sensors favorable tradeoff | ablation table | **partial** | “within evaluated configurations” |

Preferred wording used: biomechanical risk monitoring; pressure overload characterization; engineering validation; risk-alert framework; feasibility study; wearable monitoring platform.
