# Simulated program-committee decision (round 2)

Reviews: A borderline; B weak accept (methods) / borderline (clinical ML); C borderline / weak reject if oversold as deployed; D weak reject clinically / borderline methods; E borderline.

## Would this likely be accepted?

**Uncertain — simulated consensus: borderline.** A methods-oriented EHB reviewer can argue weak accept. A clinical or “show me the wearable current” reviewer can argue weak reject. This is **not** a clear accept.

## Primary reason it could be accepted

A complete, honest sparse-sensing methods package: hardware contract, grouped ML, ablation with CIs, robustness failure modes, host latency, reproducibility, conservative claims.

## Strongest rejection argument

There is still **no human plantar recording, no bench FSR calibration, and no BLE/power measurement**. High AUROC is simulator-separability. The paper is a well-documented pipeline plus an in-silico study.

## Exact change that would most improve odds

One ethics-approved walking cohort **or** even a small load-cell + over-the-air BLE characterization on the real insole — not another boosting model.

## Did we rerun after “fixing” reviews?

Yes: round 1 complained about claim inflation, IID leakage, RF-vs-logreg, missing grouped splits, and ulcer CNN in the core story. Those **solvable** issues were addressed in the last-mile + this hardening pass **without** changing reviewer rubrics to be friendlier. Physical-data gaps were **not** fabricated to raise the score. Consensus remains borderline, not accept.
