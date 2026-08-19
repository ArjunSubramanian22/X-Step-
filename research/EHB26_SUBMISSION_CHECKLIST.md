# EHB 2026 submission checklist

Do not mark an item complete unless a human or an automated check in this repo has verified it.

- [ ] official formatting verified (Springer Word template downloaded — see `FORMAT_REQUIREMENTS_TO_VERIFY.md`)
- [ ] page limit verified (compiled Springer PDF page count in 6–15)
- [ ] author information verified
- [ ] affiliations verified
- [ ] corresponding author verified
- [x] abstract drafted from registry numbers (human polish still allowed)
- [x] keywords drafted
- [ ] figures readable in the official template at print size
- [ ] tables readable in the official template
- [x] references verified against `reference_audit.csv` (DOIs); Crossref live fetch optional
- [ ] citations compile in the official template
- [x] no placeholders in `research/manuscript/main.md` (lint)
- [x] no unsupported clinical outcome claims in `main.md` (claim audit)
- [x] real/synthetic data labeled
- [x] results reproduced from frozen files via `make paper` (does not retrain)
- [ ] source archive clean (release candidate tag)
- [ ] final PDF inspected (pdflatex/`llncs` may be absent)
- [x] supplementary files prepared (`research/supplement/`)
- [x] code release prepared (public GitHub; MIT)
- [x] data availability statement prepared (synthetic; no human traces)
- [ ] ethics/consent statement accurate (no IRB number in repo — **human confirm**)
- [ ] conflict-of-interest statement accurate
- [ ] funding/acknowledgments accurate
