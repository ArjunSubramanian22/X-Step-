"""Reusable statistical helpers (bootstrap, paired tests, effect sizes)."""

from __future__ import annotations

import numpy as np
from sklearn.metrics import f1_score

from xstep_ml.evaluation.stats import bootstrap_metric, mcnemar_b


def cohens_h(p1: float, p2: float) -> float:
    """Cohen's h for two proportions."""
    return float(2 * np.arcsin(np.sqrt(p1)) - 2 * np.arcsin(np.sqrt(p2)))


def paired_macro_f1_delta(y_true: np.ndarray, y_a: np.ndarray, y_b: np.ndarray) -> dict:
    f1a = float(f1_score(y_true, y_a, average="macro", zero_division=0))
    f1b = float(f1_score(y_true, y_b, average="macro", zero_division=0))
    acc_a = float((y_a == y_true).mean())
    acc_b = float((y_b == y_true).mean())
    return {
        "macro_f1_a": f1a,
        "macro_f1_b": f1b,
        "delta_b_minus_a": f1b - f1a,
        "cohens_h_accuracy": cohens_h(acc_b, acc_a),
        "mcnemar": mcnemar_b(y_true, y_a, y_b),
    }


def bonferroni(p_values: list[float], alpha: float = 0.05) -> dict:
    m = max(len(p_values), 1)
    return {
        "m_tests": m,
        "alpha": alpha,
        "alpha_bonferroni": alpha / m,
        "reject": [float(p) < (alpha / m) for p in p_values],
        "note": "Use CIs as primary reporting; p-values are exploratory on synthetic labels.",
    }


def descriptive(x: np.ndarray) -> dict[str, float]:
    x = np.asarray(x, dtype=np.float64)
    return {
        "n": float(len(x)),
        "mean": float(np.mean(x)) if len(x) else float("nan"),
        "std": float(np.std(x, ddof=1)) if len(x) > 1 else 0.0,
        "median": float(np.median(x)) if len(x) else float("nan"),
        "min": float(np.min(x)) if len(x) else float("nan"),
        "max": float(np.max(x)) if len(x) else float("nan"),
    }


__all__ = ["bootstrap_metric", "mcnemar_b", "cohens_h", "paired_macro_f1_delta", "bonferroni", "descriptive"]
