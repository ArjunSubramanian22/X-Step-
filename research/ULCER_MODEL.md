# Ulcer photograph model — audit

## Dataset

- Public DFU grade photographs (Roboflow/Kaggle-style archive under `ulcer model/archive/`).
- **Not** paired with X-Step insole pressure.
- Images are gitignored; licensing: see `ulcer model/archive/README.dataset.txt` when present.

## Classes

Wagner-style grades 1–4 as folder names (`Grade 1` … `Grade 4`), mapped to labels 0–3 in code.

## Splits

Use `xstep_ml.data.splits.roboflow_preset_splits` / group-wise source IDs (`.rf.` siblings). Do not use notebook random 80/20.

## Training (when archive present)

`scripts/train_ulcer.py`: ImageNet-style backbones optional; lightweight CNN default. Optimizer/LR/epochs in `xstep_ml.config` and the training script. Early stopping patience `DEFAULT_PATIENCE`.

## Evaluation

Confusion matrix, per-class P/R/F1, macro-F1, AUROC if probabilities. Grad-CAM (`xstep_ml.evaluation.gradcam`) is **interpretability support**, not clinical validation.

## Duplicate images

Roboflow augmentations share a source id; grouping is required to avoid leakage.

## Status in default `make experiments`

Skipped if the archive is absent. Table 7 records that fact rather than inventing metrics.
