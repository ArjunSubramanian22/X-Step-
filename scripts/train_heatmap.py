#!/usr/bin/env python3
"""Train heatmap posture classifier with validation and optional k-fold CV."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import argparse
import json
from pathlib import Path

from xstep_ml.config import ROOT
from xstep_ml.data.heatmap import (
    build_heatmap_dataloaders,
    build_heatmap_kfold_loaders,
)
from xstep_ml.evaluation.metrics import compute_metrics, summarize_cv_results
from xstep_ml.evaluation.plots import save_evaluation_plots
from xstep_ml.models.heatmap import build_heatmap_model
from xstep_ml.training.trainer import TrainConfig, Trainer

HEATMAP_LABELS = [
    "Normal foot",
    "Left foot forward leaned",
    "Right foot forward leaned",
    "Left foot backward leaned",
    "Right foot backward leaned",
    "Left sided lean",
    "Right sided lean",
    "Left foot twisted",
    "Right foot twisted",
]


def parse_args():
    p = argparse.ArgumentParser(description="Train pressure heatmap classifier")
    p.add_argument("--architecture", default="resnet50", choices=["heat_cnn", "resnet50", "efficientnet_b0"])
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--epochs", type=int, default=50)
    p.add_argument("--lr", type=float, default=1e-4)
    p.add_argument("--patience", type=int, default=7)
    p.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "heatmap")
    p.add_argument("--cv-folds", type=int, default=0)
    p.add_argument("--data-path", type=Path, default=None)
    p.add_argument("--device", default="auto")
    return p.parse_args()


def run_single(args) -> dict:
    args.output_dir.mkdir(parents=True, exist_ok=True)
    train_loader, val_loader, test_loader, meta = build_heatmap_dataloaders(
        data_path=args.data_path,
        batch_size=args.batch_size,
    )

    model = build_heatmap_model(args.architecture, pretrained=True)
    config = TrainConfig(
        max_epochs=args.epochs,
        lr=args.lr,
        patience=args.patience,
        num_classes=9,
        output_dir=str(args.output_dir),
        device=args.device,
        label_names=HEATMAP_LABELS,
    )

    trainer = Trainer(model, config)
    trainer.fit(train_loader, val_loader)

    results = {}
    for split_name, loader in [("val", val_loader), ("test", test_loader)]:
        y_true, y_pred, y_prob = trainer.predict_loader(loader)
        metrics = compute_metrics(y_true, y_pred, y_prob, num_classes=9, label_names=HEATMAP_LABELS)
        results[split_name] = metrics
        save_evaluation_plots(y_true, y_pred, y_prob, args.output_dir / split_name, HEATMAP_LABELS, prefix="heatmap")

    with open(args.output_dir / "evaluation.json", "w") as f:
        json.dump(results, f, indent=2)

    for split, m in results.items():
        print(
            f"{split}: acc={m['accuracy']:.4f} macro_f1={m['macro_f1']:.4f} kappa={m['cohen_kappa']:.4f}"
        )
    return results


def run_cv(args) -> dict:
    fold_loaders = build_heatmap_kfold_loaders(
        data_path=args.data_path,
        batch_size=args.batch_size,
        n_splits=args.cv_folds,
    )
    fold_metrics = []

    for fold_i, (train_loader, val_loader, _) in enumerate(fold_loaders, 1):
        print(f"\n=== Fold {fold_i}/{args.cv_folds} ===")
        fold_dir = args.output_dir / f"fold_{fold_i}"
        model = build_heatmap_model(args.architecture, pretrained=True)
        config = TrainConfig(
            max_epochs=args.epochs,
            lr=args.lr,
            patience=args.patience,
            num_classes=9,
            output_dir=str(fold_dir),
            device=args.device,
            label_names=HEATMAP_LABELS,
        )
        trainer = Trainer(model, config)
        trainer.fit(train_loader, val_loader)
        y_true, y_pred, y_prob = trainer.predict_loader(val_loader)
        fold_metrics.append(compute_metrics(y_true, y_pred, y_prob, num_classes=9, label_names=HEATMAP_LABELS))

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
