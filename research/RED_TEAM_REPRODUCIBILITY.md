# Red-team reproducibility

Persona: independent researcher, public repo only, no author Slack.

## Attempted path

```bash
bash scripts/setup_env.sh
source .venv/bin/activate
make test
python research/experiments/build_registry.py
python research/experiments/generate_results.py
python -m research.build_paper
```

## Failures found and fixes in this phase

| Failure | Severity | Fix |
| --- | --- | --- |
| `make paper` did not exist; `make paper-assets` **retrains** | High | Added `make paper` / `python -m research.build_paper` that **does not train** |
| `generate_tables.py` exited 1 without `research_results.json` | Medium | Degraded to frozen-CSV mode |
| Canonical numbers lived in prose with extra decimals | High | `final_results_registry.json` + rounded `generated_results.md` |
| `docs/MODEL_CARD.md` pointed at missing `papers/ehb2026/tables/ehb_results.json` | Medium | Point to `research/tables/model_comparison.csv` |
| `CITATION.cff` claimed “prevention” | Claim | Title corrected |
| `dist/` gitignored, so a bundle would vanish | Medium | Allow `dist/ehb26/` |
| Matplotlib may abort in some sandboxes | Env | Document `make paper` on a real desktop; CI already runs `generate_figures` |
| `pdflatex` / `llncs.cls` often absent | Expected | Markdown is canonical; compile status written to dist |
| Human data path empty | Blocker for Level C | Importer + protocol documented; do not fabricate |

## Remaining undocumented steps (honest)

1. Official Springer Word template must be downloaded by a human.
2. EasyChair account and PDF ≤2 MB check.
3. Physical BLE/power/calibration still require hardware.
4. Ulcer CNN weights/images are gitignored on purpose.

## Status

Synthetic paper tables are regenerable from frozen files without training. Full experiment regeneration remains `make experiments` and will **move numbers** if sklearn versions change — do not do that after the submission freeze without a new manifest.
