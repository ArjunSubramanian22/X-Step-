# Sparse Four-Site Plantar-Pressure Sensing for Continuous Risk Monitoring

**Blind manuscript for EHB 2026.** Do not include author names. Quantitative Results: copy `research/manuscript/generated_results.md`. Official length/template: paste into the EHB/Springer source before upload.

**Validation in the accompanying repository:** synthetic 4-FSR cohort only. No human walking files.

## Abstract

Continuous plantar-pressure monitoring is relevant to diabetic-foot mechanics, but dense arrays are costly. We describe a four-site FSR insole (first, second, and fifth metatarsal heads and heel), 25 Hz BLE streaming with a 28-byte payload, a documented biomechanical feature set, grouped machine-learning baselines, sensor ablation, robustness to simulated wearable faults, and host-side latency. All numerical ML results use a 24-virtual-subject generator with subject-grouped cross-validation. The work does not estimate ulcer-prevention rates, diagnostic accuracy in patients, or regulatory clearance. A mobile app is supporting infrastructure; risk is computed deterministically, not by a language model.

**Keywords:** plantar pressure; sparse sensing; wearable insole; robustness; e-health

## 1. Introduction

Peak plantar pressure and pressure-time integral are established mechanical markers in diabetic foot literature. Dense laboratory systems capture spatial maps at high hardware cost. Sparse wearables require evidence that reduced sensing still preserves usable information, and that models are evaluated without mixing one person’s windows across train and test.

**Gaps:** (i) four-site layouts need ablation, not slogans; (ii) IID window accuracy is optimistic; (iii) noise, packet loss, and latency are deployment constraints.

We ask whether a low-cost four-site insole can preserve enough plantar information for continuous **pressure-risk monitoring** while remaining computationally practical. We do not ask whether the device prevents ulcers.

Contributions: four-site architecture; end-to-end ADC–BLE–feature–risk pipeline; grouped baselines and ablation; robustness curves; host latency (radio/battery unmeasured).

## 2–9.

Use `research/manuscript/main.md` as the canonical full text (methods, limitations, verified references). This blind file must not reintroduce image-CNN fusion, chatbot novelty, market size, or RF-vs-logreg rankings that contradict `research/tables/`.

## References

See `research/manuscript/main.md` and `research/manuscript/reference_audit.csv`. Fernando et al. is **2014** PLoS ONE 9(6):e99050. IWGDF 2023 update authors: Schaper, van Netten, Apelqvist, Bus, Fitridge, Game, Monteiro-Soares, Senneville.
