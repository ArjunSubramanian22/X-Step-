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
