# Novelty argument

## What this paper is not

X-Step is not novel for “building a smart insole.” Embedded FSR insoles and footwear wearables already exist [Hegde 2014 SmartStep; Hegde 2016 review]. Dense plantar arrays already exist [Razak 2012]. Temperature home monitoring already has RCT evidence [Armstrong 2007; Lavery 2007; Frykberg 2017]. We do **not** claim that no prior work exists, and we do **not** claim higher accuracy than Pedar-class systems or temperature trials.

## What is actually supported

The supported combination is:

1. **Sparse, clinically motivated sensing** — four sites at MET1, MET2, MET5, HEEL, documented in firmware and schema, not a marketing four-zone cartoon.
2. **Low hardware complexity** — FSR402-class + ESP32 + 28-byte BLE, specified rather than implied.
3. **Quantitative sensor ablation** — grouped-CV macro-F1 as channels are removed, with CIs, including the finding that MET1 is nearly redundant with the other three **on this simulator** while MET5 and HEEL are not.
4. **Grouped (subject-independent) ML** — IID reported only as an optimistic control.
5. **Robustness under wearable-like imperfections** — noise, bias, missing channels, simulated packet loss, sampling-rate reduction, with failure modes shown.
6. **Host real-time characterization** — feature + logreg latency and model size, with radio/battery explicitly out of scope.
7. **Reproducible end-to-end implementation** — tests, freeze, importer, `make paper` that does not silently retrain.

## Contrast with typical prior work

| Typical prior pattern | What X-Step adds here |
| --- | --- |
| Dense lab map, offline analysis | Sparse daily-wear **contract** + ablation of that contract |
| Sparse insole for activity/energy | Overload-pattern **characterization** on plantar pressure features |
| Single accuracy number on mixed windows | Subject-grouped vs IID comparison |
| Hardware paper without ML operating curves | Perturbation sweeps |
| ML paper without a packet spec | 28-byte v1 payload + 25 Hz firmware constant |
| Clinical RCT (temperature) | Not claimed; different modality |

## Citation rule

Every comparison sentence in Related Work has a verified numbered reference. If a comparison cannot be cited, it is deleted.
