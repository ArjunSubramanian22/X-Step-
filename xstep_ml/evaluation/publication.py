"""Publication-grade classification and regression metrics with CIs."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)
from sklearn.preprocessing import label_binarize


def _safe_auc(y_true: np.ndarray, y_prob: np.ndarray, labels: list) -> float | None:
    try:
        if y_prob.ndim != 2:
            return None
        y_bin = label_binarize(y_true, classes=labels)
        if y_bin.shape[1] == 1:
            return float(roc_auc_score(y_true, y_prob[:, 1] if y_prob.shape[1] > 1 else y_prob[:, 0]))
        return float(roc_auc_score(y_bin, y_prob, average="macro", multi_class="ovr"))
    except ValueError:
        return None


def _safe_ap(y_true: np.ndarray, y_prob: np.ndarray, labels: list) -> float | None:
    try:
        y_bin = label_binarize(y_true, classes=labels)
        return float(average_precision_score(y_bin, y_prob, average="macro"))
    except ValueError:
        return None


def expected_calibration_error(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> dict[str, float]:
    """Top-label ECE and bin centers for a reliability diagram."""
    conf = y_prob.max(axis=1)
    pred = np.argmax(y_prob, axis=1)
    # map labels to 0..C-1 if needed
    if y_true.dtype.kind in {"U", "O", "S"}:
        return {"ece": float("nan"), "n": float(len(y_true))}
    y_int = y_true.astype(int)
    correct = (pred == y_int).astype(np.float64)
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    bin_conf, bin_acc, bin_n = [], [], []
    for i in range(n_bins):
        lo, hi = bins[i], bins[i + 1]
        mask = (conf > lo) & (conf <= hi) if i > 0 else (conf >= lo) & (conf <= hi)
        if not mask.any():
            bin_conf.append(float("nan"))
            bin_acc.append(float("nan"))
            bin_n.append(0.0)
            continue
        acc_i = float(correct[mask].mean())
        conf_i = float(conf[mask].mean())
        ece += (mask.mean()) * abs(acc_i - conf_i)
        bin_conf.append(conf_i)
        bin_acc.append(acc_i)
        bin_n.append(float(mask.sum()))
    return {
        "ece": float(ece),
        "bin_confidence": bin_conf,  # type: ignore[dict-item]
        "bin_accuracy": bin_acc,  # type: ignore[dict-item]
        "bin_count": bin_n,  # type: ignore[dict-item]
    }


def _brier_multiclass(y_true: np.ndarray, y_prob: np.ndarray, labels: list) -> float | None:
    try:
        y_bin = label_binarize(y_true, classes=labels)
        if y_bin.shape[1] != y_prob.shape[1]:
            return None
        return float(np.mean(np.sum((y_prob - y_bin) ** 2, axis=1)))
    except Exception:
        return None


def classification_suite(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: np.ndarray | None = None,
    *,
    labels: list | None = None,
) -> dict:
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    labels = list(labels) if labels is not None else sorted(set(y_true) | set(y_pred), key=str)
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    # specificity: treat each class vs rest
    spec = []
    for i, _lab in enumerate(labels):
        tp = cm[i, i]
        fn = cm[i, :].sum() - tp
        fp = cm[:, i].sum() - tp
        tn = cm.sum() - tp - fn - fp
        spec.append(float(tn / (tn + fp)) if (tn + fp) else 0.0)
    per_class = {}
    prec = precision_score(y_true, y_pred, labels=labels, average=None, zero_division=0)
    rec = recall_score(y_true, y_pred, labels=labels, average=None, zero_division=0)
    f1c = f1_score(y_true, y_pred, labels=labels, average=None, zero_division=0)
    for i, lab in enumerate(labels):
        per_class[str(lab)] = {
            "precision": float(prec[i]),
            "recall": float(rec[i]),
            "f1": float(f1c[i]),
            "specificity": spec[i],
            "support": int(cm[i, :].sum()),
        }
    out: dict = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "precision_macro": float(precision_score(y_true, y_pred, average="macro", zero_division=0)),
        "recall_macro": float(recall_score(y_true, y_pred, average="macro", zero_division=0)),
        "specificity_macro": float(np.mean(spec)) if spec else 0.0,
        "f1": float(f1_score(y_true, y_pred, average="binary", zero_division=0)) if len(labels) == 2 else float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
        "confusion_matrix": cm.tolist(),
        "labels": [str(x) for x in labels],
        "per_class": per_class,
        "data_source_note": "metrics describe the provided labels only; they are not clinical diagnostic performance unless labels are clinical outcomes",
    }
    if y_prob is not None:
        yp = np.asarray(y_prob, dtype=np.float64)
        out["auroc_macro"] = _safe_auc(y_true, yp, labels)
        out["pr_auc_macro"] = _safe_ap(y_true, yp, labels)
        out["brier"] = _brier_multiclass(y_true, yp, labels)
        if y_true.dtype.kind not in {"U", "O", "S"}:
            out["calibration"] = expected_calibration_error(y_true, yp)
        else:
            # map string labels to column order if classes_ match labels
            lab_to_i = {str(lab): i for i, lab in enumerate(labels)}
            y_int = np.array([lab_to_i[str(v)] for v in y_true], dtype=int)
            out["calibration"] = expected_calibration_error(y_int, yp)
    return out


def regression_suite(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    yt = np.asarray(y_true, dtype=np.float64)
    yp = np.asarray(y_pred, dtype=np.float64)
    mae = float(mean_absolute_error(yt, yp))
    rmse = float(np.sqrt(mean_squared_error(yt, yp)))
    return {
        "mae": mae,
        "rmse": rmse,
        "r2": float(r2_score(yt, yp)) if len(yt) > 1 else float("nan"),
    }


def bland_altman(y_ref: np.ndarray, y_new: np.ndarray) -> dict[str, float]:
    a = np.asarray(y_ref, dtype=np.float64)
    b = np.asarray(y_new, dtype=np.float64)
    mean = (a + b) / 2.0
    diff = b - a
    md = float(diff.mean())
    sd = float(diff.std(ddof=1)) if len(diff) > 1 else 0.0
    return {
        "mean_diff": md,
        "loa_lo": md - 1.96 * sd,
        "loa_hi": md + 1.96 * sd,
        "sd_diff": sd,
        "n": float(len(diff)),
        "mean_level_mean": float(mean.mean()),
    }


def bootstrap_ci(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    metric_fn: Callable[[np.ndarray, np.ndarray], float],
    *,
    n_boot: int = 400,
    seed: int = 67,
    y_prob: np.ndarray | None = None,
) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    n = len(y_true)
    stats = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        if y_prob is None:
            stats.append(float(metric_fn(y_true[idx], y_pred[idx])))
        else:
            stats.append(float(metric_fn(y_true[idx], y_pred[idx])))  # metric_fn may ignore prob
    arr = np.asarray(stats, dtype=np.float64)
    return {
        "mean": float(arr.mean()),
        "std": float(arr.std(ddof=1)) if len(arr) > 1 else 0.0,
        "ci95_lo": float(np.percentile(arr, 2.5)),
        "ci95_hi": float(np.percentile(arr, 97.5)),
    }


def bootstrap_macro_f1(y_true: np.ndarray, y_pred: np.ndarray, n_boot: int = 400, seed: int = 67) -> dict[str, float]:
    def _f1(a, b):
        return f1_score(a, b, average="macro", zero_division=0)

    return bootstrap_ci(y_true, y_pred, _f1, n_boot=n_boot, seed=seed)
