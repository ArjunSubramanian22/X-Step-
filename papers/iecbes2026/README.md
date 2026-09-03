# X-Step — IECBES 2026 submission package

IEEE two-column manuscript for the **IEEE-EMBS Conference on Biomedical
Engineering and Sciences (IECBES 2026)**, 9–11 December 2026, Kuala Lumpur.

## Contents

```
main.tex                  the manuscript (target: 6 pages)
main.pdf                  last PDF build (rebuild after fill-ins; see COMPILE_STATUS.txt)
COMPILE_STATUS.txt        pdflatex availability note
IEEEtran.cls              IEEE conference class, V1.8b (Overleaf also ships it)
figs/fig1_system.pdf      sensor layout + acquisition-to-alert pipeline
figs/fig2_layout.pdf      layout value on the macro-F1 and Fano information scales
figs/fig3_budget.pdf      fault sensitivity + applied fault vs. transducer budget
figs/make_figures.py      regenerates all three figures (matplotlib + numpy)
README.md                 this file
```

## Building on Overleaf

1. **New Project → Upload Project** and select the zip.
2. Set the main document to `main.tex` (Menu → Main document).
3. Compiler: **pdfLaTeX**. No bibtex run is needed — the bibliography is a
   `thebibliography` environment inside `main.tex`.

Locally: `pdflatex main && pdflatex main` (twice, for cross-references).

Figures are vector PDFs. To change them, edit `figs/make_figures.py` and run
`python3 make_figures.py` from inside `figs/`. Every number it plots comes from
the results tables in `main.tex`; nothing there is simulated.

## IECBES 2026 conformance

Checked against <https://www.iecbes.org/paper_submission.php>:

| Requirement | Status |
|---|---|
| A4 paper (21.0 × 29.7 cm) | `a4paper` class option; output measures 595 × 842 pt |
| IEEE two-column conference format | `\documentclass[10pt,conference,a4paper]{IEEEtran}` |
| 10 pt body text | set |
| Six-page limit, incl. references | source updated; rebuild PDF and confirm 6 pages |
| No page numbers | IEEEtran `conference` mode suppresses them |
| All authors listed on page 1 | filled; review is *single*-blind, so do **not** anonymise |
| IEEE PDF eXpress for camera-ready | conference ID `69346x` |

Submission deadline was extended to **15 September 2026** (Malaysia time), via
EDAS. Confirm this on the site before relying on it.

## Before you submit

### 1. Author block

Authors are listed on page 1. IECBES review is *single*-blind; do **not**
anonymise.

### 2. Fill-in quantities (done)

The seven former `\fillin{...}` slots were computed by
`research/experiments/iecbes_fillins.py` from the frozen synthetic cohort
(seed 67) and the operator-attested calibration CSV. Summary:

1. Subject-cluster bootstrap CI ($B=2000$): production macro-F1 0.885 [0.861--0.907]
2. Holm-adjusted $p$ vs dummy (family of 8): $4\times10^{-3}$ (resolution of $B=2000$)
3. TOST logreg vs HGB at $\delta=0.02$: equivalent; 90% CI $[-0.0197,0.0151]$, $p=0.047$
4. Per-site $(k_c,b_c)$ from the resistance log--log fit that yields MAE 1.69 N
5. Best two-site layout is **MET2+HEEL** (0.686), not MET5+HEEL (0.649)
6. Per-layout accuracies are in Table II; Fano $P_e$ uses accuracy, not macro-F1
7. Shapley values: MET1 0.152, MET2 0.158, MET5 0.254, HEEL 0.280

### 3. If it runs long after your edits

Cut in this order (also noted in the header comment of `main.tex`):

1. the gain-invariance remark at the end of Sec. II-D
2. the Nyquist argument in Sec. IV-D
3. the convex-hull bound in Sec. IV-E
4. merge Table III into the text of Sec. IV-D
5. drop Fig. 1(a) and keep only the pipeline panel

## What changed relative to the earlier (LNCS/EHB) draft

Reformatted for IEEE, and the analysis was deepened rather than just
reformatted:

- **Fano bound (new, Sec. IV-B, Table II).** Macro-F1 is converted into a
  distribution-free lower bound on retained label information. The four-site
  window keeps ≥ 2.310 of the 3.170 bits of label entropy (72.9%). The bound is
  tight at chance — the majority dummy returns exactly 0.000 bits, which is a
  useful check on the arithmetic.
- **Two-scale cooperative game (Sec. IV-C).** Marginal contributions recover
  only 54% of the attainable macro-F1 but 91% of the attainable information, so
  most of the apparent redundancy is an artefact of the concave F1 scale rather
  than a property   of the sensor set. The MET1–MET2 interaction survives the
  change of scale (+0.223 F1, +1.001 bits) while MET5/HEEL flips from mildly
  superadditive to mildly subadditive (−0.315 bits).
- **Remark 1 (Sec. II-D).** A short proof that subtracting a per-window low
  quantile makes every feature invariant to a constant offset, since quantiles
  are translation-equivariant. This converts the paper's worst failure mode
  (−0.666 macro-F1 under a +15 kPa offset) from a finding into a fixable bug.
- **Sensitivity of the calibration model (eq. 2).** Relative force error is
  amplified by the exponent *b_c* and diverges near the unloaded baseline —
  which is where the 30 kPa contact threshold sits.
- **Convex-hull bound on CoP (Sec. IV-E).** A four-point measure confines the
  centre-of-pressure estimate to the convex hull of the site coordinates, so it
  systematically contracts true excursion. This explains the near-zero
  mediolateral correlation geometrically, not just empirically.
- Explicit error budget in pressure units (Fig. 3b), design-effect calculation,
  Holm–Bonferroni, TOST, Nadeau–Bengio caveat, three named estimands, and fault
  operators stated precisely enough to distinguish a bound from an estimate.

## Standing caveat

All machine-learning results are derived from a synthetic 24-subject generator.
No X-Step four-site human walking data exist in this release (*N* = 0). The
paper contributes engineering and algorithmic evidence only, and makes no
claim about ulcer prediction, screening performance or clinical benefit.
