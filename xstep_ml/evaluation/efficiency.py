"""Model size, parameter count, and inference latency helpers."""

from __future__ import annotations

import io
import time
from typing import Any

import joblib
import numpy as np


def _n_params(estimator: Any) -> int | None:
    clf = estimator
    if hasattr(estimator, "named_steps"):
        clf = estimator.named_steps.get("clf", estimator)
    n = 0
    found = False
    for attr in ("coef_", "intercept_", "tree_", "estimators_"):
        if not hasattr(clf, attr):
            continue
        val = getattr(clf, attr)
        if attr == "estimators_" and isinstance(val, (list, np.ndarray)):
            found = True
            for est in np.asarray(val, dtype=object).ravel():
                inner = _n_params(est)
                if inner:
                    n += inner
            continue
        if hasattr(val, "ravel"):
            found = True
            n += int(np.asarray(val).size)
    if hasattr(clf, "n_features_in_") and hasattr(clf, "classes_") and hasattr(clf, "coef_"):
        found = True
    return int(n) if found else None


def serialized_size_bytes(estimator: Any) -> int:
    buf = io.BytesIO()
    joblib.dump(estimator, buf)
    return int(buf.tell())


def inference_latency(
    estimator: Any,
    X: np.ndarray,
    *,
    n_warmup: int = 5,
    n_repeat: int = 40,
) -> dict[str, float]:
    x = np.asarray(X)
    if len(x) == 0:
        raise ValueError("empty X")
    # warmup
    for _ in range(n_warmup):
        estimator.predict(x[: min(16, len(x))])
    times = []
    row = x[:1]
    for _ in range(n_repeat):
        t0 = time.perf_counter()
        estimator.predict(row)
        times.append((time.perf_counter() - t0) * 1000.0)
    arr = np.asarray(times, dtype=np.float64)
    return {
        "mean_ms": float(arr.mean()),
        "median_ms": float(np.median(arr)),
        "p95_ms": float(np.percentile(arr, 95)),
        "std_ms": float(arr.std(ddof=1)) if len(arr) > 1 else 0.0,
        "n": float(len(arr)),
    }


def model_efficiency_row(name: str, estimator: Any, X: np.ndarray) -> dict:
    lat = inference_latency(estimator, X)
    size = serialized_size_bytes(estimator)
    return {
        "model": name,
        "n_params": _n_params(estimator),
        "serialized_bytes": size,
        "serialized_kb": round(size / 1024.0, 2),
        **lat,
        "runtime": "cpython-sklearn",
    }
