# Four-Site Plantar Pressure Sensing and Machine Learning for Early Diabetic Foot Ulcer Risk Stratification

**Blind manuscript for EHB 2026 (Springer / IFMBE Proceedings).** Do not include author names or affiliations in this file. Target length: 6 pages in the official Springer one-column template (paste into the EHB Word template before EasyChair upload). English (USA). Figures are 300 dpi PNG and vector PDF under `figures/`.

## Abstract

Diabetic foot ulcers (DFUs) remain a leading cause of hospitalization and amputation, yet peak plantar pressure, pressure-time integral, and thermal asymmetry are measurable before tissue breakdown. Dense instrumented mats and clinical insoles can capture these signals, but they are costly and poorly suited to unsupervised daily wear. We present X-Step, an end-to-end preventive pipeline built around four force-sensitive resistors placed at the first, second, and fifth metatarsal heads and the heel—sites repeatedly implicated in neuropathic ulceration. A 25 Hz Bluetooth Low Energy stream is converted into a compact biomechanical feature set (peak pressure, pressure-time integral, loading fraction, left–right asymmetry, cadence, and anterior–posterior center of pressure). A random forest classifies gait overload patterns; a gradient-boosting model flags the dominant high-risk zone; an IWGDF-inspired clinical prior and an optional wound-image CNN are fused into a 0–100 health index with conservative, sensor-grounded alerts. Because paired insole-and-outcome cohorts are still being collected, we evaluate the pressure branch in silico on a 24-subject virtual cohort that injects mass scaling, FSR gain mismatch, offset drift, label noise, and mixed overload severity. Under 5-fold subject-grouped cross-validation, the random forest outperforms logistic regression and a majority baseline on macro-F1, with permutation importance concentrated on peak and asymmetry features. We report bootstrap 95% confidence intervals, feature ablation, and noise-robustness curves, and we state clearly that these results do not substitute for a prospective clinical trial. The contribution is a reproducible wearable-plus-ML architecture aligned with DFU biomechanics and with the EHB themes of wearable sensors, biosignal processing, and AI in medicine.

**Keywords:** diabetic foot ulcer, plantar pressure, wearable insole, gait analysis, machine learning, e-health

## 1 Introduction

More than 30 million people worldwide live with or will develop a DFU. Five-year mortality after ulceration approaches 50% in several series, and roughly one in three affected patients undergoes amputation. Treatment costs routinely exceed USD 15 000 per episode. The tragedy, from a bioengineering standpoint, is that the mechanical pathway is well described: peripheral neuropathy removes protective sensation, repetitive peak pressure and shear over bony prominences produce inflammation, and unnoticed tissue injury progresses to ulceration [1–3].

Screening still depends on infrequent clinic visits, 10 g monofilament tests, and patient self-inspection. Those assumptions fail in underserved communities with limited specialist access. Continuous plantar monitoring exists in two unsatisfactory forms: consumer cushioning with no sensing, and research-grade systems (pressure mats, dense insole arrays) that are accurate but expensive and clinic-bound [4,5].

X-Step is designed as a daily-wear alternative: a custom insole with **four** force-sensitive resistors (FSRs) at clinically motivated sites, a compact BLE microcontroller, on-device and server-side machine learning, and a mobile record that patients can show to clinicians. This paper does not claim a completed randomized trial. It specifies the sensing contract, the biomechanical features, the learning setup, and a **subject-grouped in-silico evaluation** that a reviewer can reproduce from the public repository. Wound-image grading uses a public four-class DFU photograph set and is treated as an auxiliary modality, not as paired ground truth for the insole.

The questions we answer are:

1. Can a four-channel plantar stream, rather than a full pressure image, still discriminate overload patterns that matter for DFU prevention?
2. Which biomechanical features carry that signal under inter-subject sensor variability?
3. How should clinical risk (IWGDF-style) and optional wound photography be fused without pretending the system is a diagnostic device?

## 2 Related Work

Peak plantar pressure (PPP) and pressure-time integral (PTI) are established mechanical risk markers [2,6]. International Working Group on the Diabetic Foot (IWGDF) guidance stratifies risk by neuropathy, peripheral artery disease, and ulcer/amputation history [7]. Plantar temperature asymmetry near 2.2 °C has been associated with pre-ulcerative inflammation [8,9].

Commercial and research wearables occupy a wide cost–density spectrum. Capacitive arrays (e.g., Moticon, Pedar) provide high spatial resolution for gait labs. Remote temperature mats (e.g., Podimetrics) target daily home use but not shoe-embedded pressure. Optical or piezoresistive research insoles often exceed consumer price points [4,5]. Machine-learning papers on DFU photographs report strong accuracy on public image sets, yet photographs arrive *after* a wound exists; they do not replace mechanical prevention [10].

Closest to this work are sparse FSR gait classifiers. Many prior studies use healthy-adult or laboratory footwear data, random (not subject-wise) splits, or do not publish a byte-level wireless protocol. We differ by (i) locking sensor order to ulcer-prone anatomy, (ii) publishing the 28-byte BLE payload, (iii) fusing IWGDF-style clinical priors, and (iv) evaluating with **grouped** validation plus noise and ablation, which is the minimum bar for a methods paper in biomedical engineering.

## 3 Methods

### 3.1 Hardware and signal model

Each insole carries four FSR402-class sensors in a 10 kΩ divider on 12-bit ADC channels:

- MET1: first metatarsal head (medial forefoot / hallux ray)
- MET2: second metatarsal head (central forefoot)
- MET5: fifth metatarsal head (lateral column)
- HEEL: calcaneus

Placement follows the observation that neuropathic ulcers cluster at the metatarsal heads and heel rather than uniformly across the plantar surface [1,6]. Left and right insoles advertise as independent BLE peripherals. Firmware packs a 28-byte little-endian frame (`magic = "XS"`): version, side flags, sequence, millisecond timestamp, four ADC samples, battery, and reserved temperature fields (for a planned thermistor array). ADC is mapped to kilopascals with a full-scale of 250 kPa after subtracting an unloaded baseline captured at onboarding. Nominal streaming rate is 25 Hz, a compromise between BLE payload rate and step-cycle sampling (a 110 step/min cadence yields roughly 13–14 samples per stance).

App-level zones (toes, ball, arch, heel) are aliases of MET1, MET2, MET5, and HEEL so that a patient-facing map remains anatomically honest.

### 3.2 Feature extraction

A window \(W \in \mathbb{R}^{T \times 8}\) stacks left then right sites. Let \(\Delta t = 1/f_s\). For each site and foot we compute peak pressure, mean pressure, PTI \(\sum p_t \Delta t\), fraction of samples above 30 kPa (loaded), fraction above 200 kPa (literature high-risk PPP band), and coefficient of variation. Bilateral asymmetry is \(|p_L - p_R| / ((p_L+p_R)/2)\) on peaks. Heel-strike peaks on the mean heel channel estimate cadence (steps/min). Anterior–posterior center-of-pressure share is the forefoot mass divided by total pressure mass. Optional thermistors contribute max contralateral temperature difference, compared against the 2.2 °C heuristic [8].

The resulting vector has 59 scalars. Features are standardized inside each model pipeline. No image CNN features enter the gait/zone experiments reported here.

### 3.3 Models

**Gait pattern** (9 classes): normal; left/right forefoot, heel, or lateral overload; asymmetric antalgic; shuffling/low cadence. We compare majority, \(\ell_2\) logistic regression, linear SVM, random forest, gradient boosting, and a two-layer MLP (all after StandardScaler except the dummy). **Production inference uses logistic regression**: it is statistically stronger than the random forest on subject-grouped data (McNemar \(p < 10^{-7}\)) and remains inspectable for a clinical methods paper. The MLP is reported as a capacity ceiling.

**High-risk zone** (MET1, MET2, MET5, HEEL, none): gradient boosting.

**High-risk zone** (MET1, MET2, MET5, HEEL, none): gradient boosting (80 trees, depth 3).

**Clinical prior:** a transparent score approximating IWGDF categories 0–3 from neuropathy, HbA1c, ulcer/amputation history, smoking, and occupational standing [7]. It is not learned from the synthetic pressure data.

**Fusion health index:** a clipped linear combination of clinical score, scaled PPP, thermal asymmetry, gait-pattern penalty, optional ulcer-grade term, and a small non-adherence penalty. Alerts fire when instantaneous site pressure exceeds an onboarding threshold (default 75 kPa), independent of the classifier, so the safety path is not solely model-dependent.

**Wound CNN:** a lightweight 4-class network (and optional ImageNet backbones) trained on a public DFU photograph corpus. In this paper it is an auxiliary module; we do not claim paired insole–photo labels.

### 3.4 In-silico cohort (pressure branch)

Real insole traces with ulcer endpoints are not in this repository. To avoid IID leakage on trivial sinusoids, we generate **virtual subjects**. Each subject draws mass scale \(\in [0.78, 1.32]\), per-channel FSR gain \(\in [0.82, 1.18]\), kPa offset noise, cadence bias, and a small dropout probability. Overload severity is mixed (mild to severe), 3% of window labels are flipped, and Gaussian noise SD is 3.5 kPa unless swept. Default cohort: 24 subjects \(\times\) 9 patterns \(\times\) 12 windows (4 s at 25 Hz) = 2592 labeled windows.

This is a **simulation study**. It tests whether the feature set and models remain identifiable under plausible hardware mismatch. It does **not** estimate clinical sensitivity for ulcer incidence.

### 3.5 Experimental protocol

Primary protocol: **5-fold GroupKFold** by subject ID (no window from a subject appears in both train and test). Metrics: accuracy and macro-F1 with 1000-bootstrap 95% confidence intervals on pooled out-of-fold predictions; mean \(\pm\) SD of per-fold macro-F1. Pairwise comparison of random forest vs logistic regression uses a continuity-corrected McNemar test. Ablation removes asymmetry or temporal features, or keeps peaks only. Robustness: train at 3.5 kPa noise, test held-out subjects regenerated at 1.5, 3.5, 7, and 12 kPa. Permutation importance (macro-F1, 8 repeats) is computed on a six-subject hold-out. All seeds are fixed (67). Code: `scripts/run_ehb_experiments.py`.

### 3.6 Ethics and intended use

No identifiable patient telemetry is released. DFU photographs, when used, come from a public classification set. X-Step in this form is a **research prototype**, not an FDA-cleared device, and messages are educational. A future prospective study requires IRB review, informed consent, and predefined clinical endpoints (peak pressure reduction, pre-ulcerative lesion incidence).

## 4 Results

Cohort: 24 virtual subjects, 2592 windows, 5-fold GroupKFold by subject, 3% label noise, mixed overload severity (seed 67). Table 1 is `papers/ehb2026/tables/table1_baselines.md`.

**Table 1.** Gait-pattern classification, subject-grouped CV, bootstrap 95% CI.

| Model | Accuracy | Macro-F1 | Fold macro-F1 mean (SD) |
| --- | --- | --- | --- |
| majority | 0.109 [0.097, 0.122] | 0.051 [0.045, 0.058] | 0.022 (0.000) |
| logreg | 0.872 [0.859, 0.885] | 0.871 [0.859, 0.883] | 0.875 (0.035) |
| linear SVM | 0.873 [0.860, 0.885] | 0.871 [0.859, 0.884] | 0.875 (0.036) |
| random forest | 0.834 [0.820, 0.849] | 0.837 [0.824, 0.851] | 0.842 (0.031) |
| GBM | 0.865 [0.852, 0.879] | 0.866 [0.854, 0.880] | 0.869 (0.034) |
| MLP | 0.885 [0.872, 0.896] | 0.884 [0.871, 0.894] | 0.885 (0.020) |

A stratified IID split of the same windows inflates logistic-regression accuracy to \(\approx 0.92\). We therefore **do not report IID scores as the paper result**; GroupKFold by subject is the protocol. Logistic regression significantly outperformed the random forest (McNemar \(\chi^2 = 32.1\), \(p \approx 1.4 \times 10^{-8}\); 199 windows where logreg was uniquely correct vs 100 the other way). The MLP is the numerical best but only about 1.3 points of macro-F1 above logreg. **Normal gait is the hardest class** (RF per-class F1 \(\approx 0.60\)), which is expected: mild overload was deliberately mixed into the generator so that “normal” is not a distant cluster. Forefoot overload remains the easiest localization (F1 \(> 0.88\)).

Peak-only features retain macro-F1 \(\approx 0.85\) (RF ablation); dropping asymmetry hurts more than dropping cadence. On six held-out subjects, FSR noise SD of 1.5 / 3.5 / 7 / 12 kPa yields macro-F1 0.88 / 0.85 / 0.75 / 0.48, i.e., cheap piezoresistive noise is a first-order failure mode. Zone GBM hold-out macro-F1 is 0.913 [0.892, 0.937]; this head is easier because zone is a deterministic function of pattern in the simulator and must not be over-interpreted clinically.

Figures (300 dpi PNG and vector PDF in `figures/`):

- Fig. 1 system pipeline (`fig_system`)
- Fig. 2 grouped-CV confusion matrix (`fig_gait_confusion`)
- Fig. 3 baseline macro-F1 with 95% CI (`fig_baselines`)
- Fig. 4 feature ablation (`fig_ablation`)
- Fig. 5 noise robustness (`fig_noise`)
- Fig. 6 permutation importance (`fig_importance`)

## 5 Discussion

Four sensing sites cannot reconstruct a full plantar pressure map. They can, however, track the locations that dominate DFU mechanics if the device is worn consistently and calibrated. Linear models beating an untuned forest is a **feature-quality result**, not a failure: PPP and asymmetry already encode the labels we defined. Remaining errors concentrate on the normal class under mild overload—the regime that matters clinically and that a gait lab must measure next. We refuse to headline IID 99% accuracy from an earlier toy generator.

Limitations: no human gait-lab gold standard in this release; FSR hysteresis and shear are not modeled; temperature channels are reserved; ulcer CNN labels are photographic grades, not Wagner outcomes tied to the same foot-steps; fusion weights are specified, not learned on clinical endpoints. These are appropriate caveats for EHB, not reasons to hide the system.

Implications: a reproducible BLE contract and feature list let other labs swap in capacitive sensors or add IMUs without rewriting the mobile stack. The conservative alert path (threshold OR model) is deliberate for a prevention product.

## 6 Conclusion

X-Step couples a four-site plantar insole to biomechanical features, grouped-validation ML, and a clinical prior for DFU risk communication. In-silico subject-wise experiments support the claim that sparse FSRs, correctly placed, encode overload patterns beyond a naive baseline. Prospective insole logging—already begun in clinical partnership—is the necessary next measurement, not more network depth on synthetic steps.

## Acknowledgments

Removed for double-blind review.

## Conflict of interest

Removed for double-blind review. A patent-pending hardware disclosure may exist; it does not alter the methods reproducibility of this software.

## References

1. Armstrong DG, Boulton AJM, Bus SA (2017) Diabetic foot ulcers and their recurrence. N Engl J Med 376:2367–2375
2. Bus SA, van Deursen RW, Armstrong DG, Lewis J, Caravaggi CF, Cavanagh PR (2016) Footwear and offloading interventions to prevent and heal foot ulcers and reduce plantar pressure in patients with diabetes: a systematic review. Diabetes Metab Res Rev 32(S1):99–118
3. Singh N, Armstrong DG, Lipsky BA (2005) Preventing foot ulcers in patients with diabetes. JAMA 293:217–228
4. Hegde N, Bries M, Sazonov E (2016) A comparative review of footwear-based wearable systems. Electronics 5(3):48
5. Abdul Razak AH, Zayegh A, Begg RK, Wahab Y (2012) Foot plantar pressure measurement system: a review. Sensors 12:9884–9912
6. Fernando ME, Crowther RG, Pappas E, Lazzarini PA, Cunningham M, Sangla KS, Buttner P, Golledge J (2015) Plantar pressure in diabetic peripheral neuropathy patients with active foot ulceration, previous ulceration and no history of ulceration: a meta-analysis of observational studies. PLoS ONE 10(6):e0127738
7. Schaper NC, van Netten JJ, Apelqvist J, Bus SA, Hinchliffe RJ, Lipsky BA (2023) Practical guidelines on the prevention and management of diabetes-related foot disease (IWGDF 2023 update). Diabetes Metab Res Rev 40:e3657
8. Armstrong DG, Holtz-Neiderer K, Wendel C, Mohler MJ, Kimbriel HR, Lavery LA (2007) Skin temperature monitoring reduces the risk for diabetic foot ulceration in high-risk patients. Am J Med 120:1042–1046
9. Frykberg RG, Gordon IL, Reyzelman AM, et al. (2017) Feasibility and efficacy of a smart mat technology to predict development of diabetic plantar ulcers. Diabetes Care 40:973–980
10. Goyal M, Reeves ND, Rajbhandari S, Yap MH (2018) Robust methods for real-time diabetic foot ulcer image analysis and classification. IEEE Trans Biomed Eng / related DFU image benchmarks; we use a public four-class photographic set for the optional CNN only
11. Lavery LA, Higgins KR, Lanctot DR, et al. (2007) Preventing diabetic foot ulcer recurrence in high-risk patients: use of temperature monitoring as a self-assessment tool. Diabetes Care 30:14–20
12. Cavanagh PR, Bus SA (2010) Off-loading the diabetic foot for ulcer prevention and healing. J Vasc Surg 52:37S–43S

After acceptance, copy these numbered references into the Springer Word template. Verify each citation against the publisher PDF before camera-ready.
