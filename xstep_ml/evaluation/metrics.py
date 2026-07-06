"""Clinical and paper-ready evaluation metrics."""

from __future__ import annotations

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    cohen_kappa_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.preprocessing import label_binarize


def adjacent_grade_error_rate(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Fraction of errors that are exactly one grade away (ordinal tasks)."""
    wrong = y_true != y_pred
    if not wrong.any():
        return 0.0
    dist = np.abs(y_true[wrong].astype(int) - y_pred[wrong].astype(int))
    return float((dist == 1).mean())


def per_class_sensitivity_specificity(
    y_true: np.ndarray, y_pred: np.ndarray, num_classes: int
) -> dict[str, dict[str, float]]:
    cm = confusion_matrix(y_true, y_pred, labels=list(range(num_classes)))
    out: dict[str, dict[str, float]] = {}
    for i in range(num_classes):
        tp = cm[i, i]
        fn = cm[i, :].sum() - tp
        fp = cm[:, i].sum() - tp
        tn = cm.sum() - tp - fn - fp
        sens = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        spec = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        out[f"class_{i}"] = {"sensitivity": sens, "specificity": spec}
    return out


def compute_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: np.ndarray | None = None,
    num_classes: int = 4,
    label_names: list[str] | None = None,
) -> dict:
    names = label_names or [f"Class {i}" for i in range(num_classes)]

    metrics: dict = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_precision": float(precision_score(y_true, y_pred, average="macro", zero_division=0)),
        "macro_recall": float(recall_score(y_true, y_pred, average="macro", zero_division=0)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
        "cohen_kappa": float(cohen_kappa_score(y_true, y_pred)),
        "adjacent_grade_error_rate": adjacent_grade_error_rate(y_true, y_pred),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=list(range(num_classes))).tolist(),
        "classification_report": classification_report(
            y_true, y_pred, target_names=names, zero_division=0, output_dict=True
        ),
        "per_class_sens_spec": per_class_sensitivity_specificity(y_true, y_pred, num_classes),
    }

    if y_prob is not None and y_prob.ndim == 2:
        try:
            y_bin = label_binarize(y_true, classes=list(range(num_classes)))
            if num_classes == 2:
                metrics["roc_auc_macro"] = float(roc_auc_score(y_true, y_prob[:, 1]))
            else:
                metrics["roc_auc_macro"] = float(
                    roc_auc_score(y_bin, y_prob, average="macro", multi_class="ovr")
                )
                metrics["roc_auc_per_class"] = roc_auc_score(
                    y_bin, y_prob, average=None, multi_class="ovr"
                ).tolist()
        except ValueError:
            metrics["roc_auc_macro"] = None

    return metrics


def summarize_cv_results(fold_metrics: list[dict], keys: list[str] | None = None) -> dict:
    keys = keys or ["accuracy", "macro_f1", "macro_recall", "cohen_kappa", "adjacent_grade_error_rate"]
    summary: dict = {}
    for key in keys:
        vals = [m[key] for m in fold_metrics if key in m and m[key] is not None]
        if vals:
            summary[key] = {"mean": float(np.mean(vals)), "std": float(np.std(vals)), "values": vals}
    return summary
