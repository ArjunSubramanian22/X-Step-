"""Bootstrap confidence intervals and paired tests for paper tables."""

from __future__ import annotations

import numpy as np
from sklearn.metrics import accuracy_score, f1_score


def bootstrap_metric(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    metric: str = "macro_f1",
    n_boot: int = 1000,
    seed: int = 67,
) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    n = len(y_true)
    stats = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        yt, yp = y_true[idx], y_pred[idx]
        if metric == "accuracy":
            stats.append(accuracy_score(yt, yp))
        else:
            stats.append(f1_score(yt, yp, average="macro", zero_division=0))
    arr = np.asarray(stats, dtype=np.float64)
    return {
        "mean": float(arr.mean()),
        "std": float(arr.std(ddof=1)),
        "ci95_lo": float(np.percentile(arr, 2.5)),
        "ci95_hi": float(np.percentile(arr, 97.5)),
    }


def mcnemar_b(y_true: np.ndarray, y_a: np.ndarray, y_b: np.ndarray) -> dict[str, float]:
    """Continuity-corrected McNemar test on paired predictions."""
    a_ok = y_a == y_true
    b_ok = y_b == y_true
    n01 = int(np.sum(a_ok & ~b_ok))
    n10 = int(np.sum(~a_ok & b_ok))
    n = n01 + n10
    if n == 0:
        return {"n01": n01, "n10": n10, "chi2": 0.0, "p_approx": 1.0}
    chi2 = (abs(n01 - n10) - 1) ** 2 / n
    # chi-square 1 df survival via erfc
    from math import erfc, sqrt

    p = float(erfc(sqrt(chi2 / 2.0)))
    return {"n01": n01, "n10": n10, "chi2": float(chi2), "p_approx": p}


def coefficient_of_variation(x: np.ndarray) -> float:
    arr = np.asarray(x, dtype=np.float64)
    mean = float(np.mean(arr))
    if abs(mean) < 1e-12 or len(arr) < 2:
        return float("nan")
    return float(np.std(arr, ddof=1) / mean)


def mean_absolute_deviation(x: np.ndarray) -> float:
    arr = np.asarray(x, dtype=np.float64)
    if len(arr) == 0:
        return float("nan")
    return float(np.mean(np.abs(arr - np.mean(arr))))


def icc_1_1(ratings: np.ndarray) -> float:
    """One-way random, single-measure ICC. ``ratings`` is (n_targets, n_raters)."""
    x = np.asarray(ratings, dtype=np.float64)
    if x.ndim != 2 or x.shape[0] < 2 or x.shape[1] < 2:
        return float("nan")
    n, k = x.shape
    grand = float(x.mean())
    row_means = x.mean(axis=1)
    bms = k * float(np.sum((row_means - grand) ** 2) / (n - 1))
    wms = float(np.sum((x - row_means[:, None]) ** 2) / (n * (k - 1)))
    denom = bms + (k - 1) * wms
    if denom == 0:
        return float("nan")
    return float((bms - wms) / denom)
