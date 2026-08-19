"""Evaluation plot generation for papers."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.metrics import ConfusionMatrixDisplay, roc_curve, auc
from sklearn.preprocessing import label_binarize

plt.rcParams.update({"figure.dpi": 300, "savefig.dpi": 300, "savefig.bbox": "tight"})


def save_evaluation_plots(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: np.ndarray | None,
    output_dir: Path | str,
    label_names: list[str],
    prefix: str = "model",
) -> None:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    _plot_confusion_matrix(y_true, y_pred, label_names, output_dir / f"{prefix}_confusion_matrix.png")
    _plot_per_class_accuracy(y_true, y_pred, label_names, output_dir / f"{prefix}_per_class_accuracy.png")

    if y_prob is not None and y_prob.ndim == 2:
        _plot_roc_curves(y_true, y_prob, label_names, output_dir / f"{prefix}_roc_curves.png")
        _plot_summary_metrics(y_true, y_pred, y_prob, output_dir / f"{prefix}_summary_metrics.png")


def _plot_confusion_matrix(y_true, y_pred, labels, path):
    fig, ax = plt.subplots(figsize=(8, 6))
    ConfusionMatrixDisplay.from_predictions(y_true, y_pred, display_labels=labels, ax=ax, cmap="Blues")
    ax.set_title("Confusion Matrix")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _plot_per_class_accuracy(y_true, y_pred, labels, path):
    accs = []
    for i in range(len(labels)):
        mask = y_true == i
        accs.append((y_pred[mask] == i).mean() if mask.any() else 0.0)

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(x=labels, y=accs, hue=labels, ax=ax, palette="viridis", legend=False)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Accuracy")
    ax.set_title("Per-class Accuracy")
    plt.xticks(rotation=30, ha="right")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _plot_roc_curves(y_true, y_prob, labels, path):
    n_classes = len(labels)
    y_bin = label_binarize(y_true, classes=list(range(n_classes)))

    fig, ax = plt.subplots(figsize=(9, 7))
    for i in range(n_classes):
        fpr, tpr, _ = roc_curve(y_bin[:, i], y_prob[:, i])
        roc_auc = auc(fpr, tpr)
        ax.plot(fpr, tpr, label=f"{labels[i]} (AUC={roc_auc:.3f})")
    ax.plot([0, 1], [0, 1], "k--", alpha=0.4)
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("ROC Curves")
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _plot_summary_metrics(y_true, y_pred, y_prob, path):
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

    metrics = {
        "Accuracy": accuracy_score(y_true, y_pred),
        "Precision": precision_score(y_true, y_pred, average="macro", zero_division=0),
        "Recall": recall_score(y_true, y_pred, average="macro", zero_division=0),
        "F1-Score": f1_score(y_true, y_pred, average="macro", zero_division=0),
    }

    fig, ax = plt.subplots(figsize=(6, 4))
    names = list(metrics.keys())
    vals = [metrics[k] for k in names]
    sns.barplot(x=names, y=vals, hue=names, ax=ax, palette="muted", legend=False)
    ax.set_ylim(0, 1.05)
    for i, v in enumerate(vals):
        ax.text(i, v + 0.02, f"{v:.3f}", ha="center", fontsize=10)
    ax.set_title("Summary Metrics")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
