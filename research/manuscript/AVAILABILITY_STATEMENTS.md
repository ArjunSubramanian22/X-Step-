# Availability statements (draft)

## Data

All quantitative ML tables in this checkout were generated from an in-repository synthetic 4-FSR gait cohort (`xstep_ml.data.synthetic_gait.make_cohort`, seed 67; hash in `research/results/manifest.json`). No human walking recordings, no identifiable telemetry, and no bench load-cell files for this hardware are present. We do **not** promise public release of participant data that the team does not have permission to share. Future ethics-approved recordings, if any, will be described in a revision of this statement.

## Code

Source code is available at https://github.com/ArjunSubramanian22/X-Step- under the MIT license. Reproducibility commands: `make test` and `make paper` (paper build does not retrain). Training, if needed, is `make experiments`. Version: use the submission release-candidate tag when minted (`v1.0-ehb26-submission-rc1`). The experimental freeze tag `v0.9-ehb26-experimental` is not moved.

## Ethics

No institutional review board protocol number is recorded in this repository. This checkout contains no identifiable participant data. Prospective human studies require review and consent; the team must confirm wording before camera-ready (`research/HUMAN_VERIFICATION_REQUIRED.md`).
