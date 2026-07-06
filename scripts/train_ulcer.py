#!/usr/bin/env python3
"""Train ulcer grading model with leakage-safe splits and transfer learning."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import argparse
import json
from pathlib import Path

import torch

from xstep_ml.config import ROOT, ULCER_ARCHIVE
from xstep_ml.data.splits import load_ulcer_manifest, stratified_group_kfold
from xstep_ml.data.ulcer import (
    UlcerImageDataset,
    build_ulcer_dataloaders,
    compute_class_weights,
    ulcer_eval_transforms,
    ulcer_train_transforms,
)
from xstep_ml.evaluation.gradcam import generate_gradcam_batch
from xstep_ml.evaluation.metrics import compute_metrics, summarize_cv_results
from xstep_ml.evaluation.plots import save_evaluation_plots
from xstep_ml.models.ulcer import build_ulcer_model
from xstep_ml.training.trainer import TrainConfig, Trainer


def parse_args():
    p = argparse.ArgumentParser(description="Train DFU ulcer grading model")
    p.add_argument("--architecture", default="efficientnet_b0", choices=["ulcer_cnn", "resnet50", "efficientnet_b0"])
    p.add_argument("--loss", default="cross_entropy", choices=["cross_entropy", "focal", "ordinal"])
    p.add_argument("--image-size", type=int, default=224)
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--epochs", type=int, default=50)
    p.add_argument("--lr", type=float, default=1e-4)
    p.add_argument("--patience", type=int, default=7)
    p.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "ulcer")
    p.add_argument("--split-mode", default="groupwise", choices=["roboflow", "groupwise"])
    p.add_argument("--cv-folds", type=int, default=0, help="If >0, run group-wise k-fold CV instead of single train")
    p.add_argument("--gradcam", action="store_true", help="Save Grad-CAM examples after training")
    p.add_argument("--device", default="auto")
    return p.parse_args()


def run_single(args) -> dict:
    args.output_dir.mkdir(parents=True, exist_ok=True)
    train_loader, val_loader, rf_valid_loader, test_loader, _, meta = build_ulcer_dataloaders(
        archive_root=ULCER_ARCHIVE,
        image_size=args.image_size,
        batch_size=args.batch_size,
        split_mode=args.split_mode,
    )
    print(f"Split strategy: {meta.get('split_strategy', args.split_mode)}")

    label_names = [f"Grade {i}" for i in range(1, 5)]
    weights = compute_class_weights(meta["labels"]) if True else None

    model = build_ulcer_model(args.architecture, pretrained=True)
    if args.architecture == "ulcer_cnn" and args.image_size != 64:
        print("Note: ulcer_cnn baseline expects 64x64; consider --image-size 64 for fair baseline.")

    config = TrainConfig(
        max_epochs=args.epochs,
        lr=args.lr,
        patience=args.patience,
        loss=args.loss,
        num_classes=4,
        output_dir=str(args.output_dir),
        device=args.device,
        label_names=label_names,
    )

    trainer = Trainer(model, config, class_weights=weights)
    trainer.fit(train_loader, val_loader)

    results = {}
    for split_name, loader in [
        ("roboflow_valid", rf_valid_loader),
        ("test", test_loader),
    ]:
        y_true, y_pred, y_prob = trainer.predict_loader(loader)
        metrics = compute_metrics(y_true, y_pred, y_prob, num_classes=4, label_names=label_names)
        results[split_name] = metrics

        plot_dir = args.output_dir / split_name
        save_evaluation_plots(y_true, y_pred, y_prob, plot_dir, label_names, prefix="ulcer")

    with open(args.output_dir / "evaluation.json", "w") as f:
        json.dump(results, f, indent=2)

    if args.gradcam:
        test_paths = [meta["paths"][i] for i in meta["indices"]["test"][:8]]
        generate_gradcam_batch(
            trainer.model,
            test_paths,
            args.output_dir / "gradcam",
            device=trainer.device,
            image_size=args.image_size,
        )

    print("\n=== Final Results ===")
    for split, m in results.items():
        print(
            f"{split}: acc={m['accuracy']:.4f} macro_f1={m['macro_f1']:.4f} "
            f"kappa={m['cohen_kappa']:.4f} adj_err={m['adjacent_grade_error_rate']:.4f}"
        )
    return results


def run_cv(args) -> dict:
    paths, labels, source_ids = load_ulcer_manifest(ULCER_ARCHIVE)
    folds = stratified_group_kfold(source_ids, labels, n_splits=args.cv_folds)
    fold_metrics = []

    for fold_i, (train_idx, val_idx) in enumerate(folds, 1):
        print(f"\n=== Fold {fold_i}/{args.cv_folds} ===")
        fold_dir = args.output_dir / f"fold_{fold_i}"
        fold_dir.mkdir(parents=True, exist_ok=True)

        train_ds = UlcerImageDataset(paths, labels, ulcer_train_transforms(args.image_size))
        eval_ds = UlcerImageDataset(paths, labels, ulcer_eval_transforms(args.image_size))

        train_loader = torch.utils.data.DataLoader(
            torch.utils.data.Subset(train_ds, train_idx.tolist()),
            batch_size=args.batch_size,
            shuffle=True,
        )
        val_loader = torch.utils.data.DataLoader(
            torch.utils.data.Subset(eval_ds, val_idx.tolist()),
            batch_size=args.batch_size,
            shuffle=False,
        )

        weights = compute_class_weights([labels[i] for i in train_idx])
        model = build_ulcer_model(args.architecture, pretrained=True)
        config = TrainConfig(
            max_epochs=args.epochs,
            lr=args.lr,
            patience=args.patience,
            loss=args.loss,
            num_classes=4,
            output_dir=str(fold_dir),
            device=args.device,
            label_names=[f"Grade {i}" for i in range(1, 5)],
        )
        trainer = Trainer(model, config, class_weights=weights)
        trainer.fit(train_loader, val_loader)
        y_true, y_pred, y_prob = trainer.predict_loader(val_loader)
        metrics = compute_metrics(y_true, y_pred, y_prob, num_classes=4)
        fold_metrics.append(metrics)

    summary = summarize_cv_results(fold_metrics)
    with open(args.output_dir / "cv_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print("\n=== CV Summary ===")
    for k, v in summary.items():
        print(f"{k}: {v['mean']:.4f} ± {v['std']:.4f}")
    return summary


def main():
    args = parse_args()
    if args.cv_folds > 0:
        run_cv(args)
    else:
        run_single(args)


if __name__ == "__main__":
    main()
