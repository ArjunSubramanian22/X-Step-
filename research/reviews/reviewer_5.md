# Reviewer 5 — Skeptical EHB generalist

**Score: 5.5 / 10**

## Strengths
- Narrow question (sparse sensing + robustness + host deployability) is conference-appropriate.
- Reproducible freeze, lockfile, CI smoke, tests, generated Results.
- Related-systems table does not claim superiority.
- Honest limitations list.

## Major concerns
- Novelty vs Hegde/Sazonov-style FSR insoles and Razak-reviewed commercial arrays is **incremental** without human data.
- Synthetic overload classes can be linearly separable by construction (peak_only ≈ full feature set in table `feature_ablation.csv`).
- Risk of two-paper problem if ulcer CNN or chatbot returns to the abstract.

## Minor concerns
- Artifact filename `gait_pattern_rf.joblib` is confusing.
- EHB page limits vs the amount of supplementary protocol text.

## Likely rejection reasons
“Complete software stack, no people, no bench” looks like a toolbox paper. EHB often wants at least a hardware measurement or a small walking N.

## Required fixes for a defensible submission
1. One bench calibration figure from real loads **or** N≥10 walking sessions with grouped evaluation (ethics as applicable).
2. Keep the paper one story: four-site pressure, not LLM, not unpaired photos.
3. Lead with ablation + robustness + latency, not “AI for DFU.”

## Last-mile response
Scope is frozen to the engineering question. Remaining rejection risk is **evidence**, not architecture.
