"""Tabular multimodal fusion architecture (no fabricated paired samples).

Pressure, gait-derived features, and ulcer images live on different datasets
in this repository. This module defines a late-fusion head and refuses to
train when modality keys are unpaired.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


class UnpairedModalityError(ValueError):
    """Raised when fusion is requested without aligned sample IDs."""


@dataclass
class FusionBundle:
    sample_ids: np.ndarray
    pressure: np.ndarray | None = None
    gait_features: np.ndarray | None = None
    image_embedding: np.ndarray | None = None
    y: np.ndarray | None = None


def assert_paired(*id_arrays: np.ndarray) -> None:
    arrays = [np.asarray(a) for a in id_arrays if a is not None]
    if len(arrays) < 2:
        raise UnpairedModalityError("fusion requires at least two aligned modalities")
    first = arrays[0]
    for other in arrays[1:]:
        if len(other) != len(first) or not np.array_equal(other, first):
            raise UnpairedModalityError(
                "sample IDs are not aligned across modalities; do not fabricate pairs. "
                "Collect simultaneous insole + photograph labels before claiming fusion gains."
            )


def late_fusion_matrix(bundle: FusionBundle) -> np.ndarray:
    parts = []
    ids = None
    for arr, name in (
        (bundle.pressure, "pressure"),
        (bundle.gait_features, "gait"),
        (bundle.image_embedding, "image"),
    ):
        if arr is None:
            continue
        parts.append(np.asarray(arr, dtype=np.float64))
        ids = bundle.sample_ids if ids is None else ids
    if len(parts) < 2:
        raise UnpairedModalityError("need ≥2 present modalities")
    assert_paired(*([bundle.sample_ids] * len(parts)))
    return np.concatenate(parts, axis=1)


def fusion_pipeline(random_state: int = 67) -> Pipeline:
    return Pipeline(
        [
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=400, class_weight="balanced", random_state=random_state)),
        ]
    )


def compare_unimodal_vs_fusion(
    pressure_X: np.ndarray,
    gait_X: np.ndarray,
    y: np.ndarray,
    sample_ids: np.ndarray,
) -> dict[str, str]:
    """Document-only helper: returns which comparisons are valid.

    Pressure features and gait-derived features computed from the *same window*
    are paired. Image embeddings are not paired in this repo.
    """
    assert_paired(sample_ids, sample_ids)
    return {
        "pressure_only": "valid when pressure_X is present",
        "gait_features_only": "valid when gait_X is a feature subset of the same windows",
        "pressure_plus_gait": "valid (same-window concatenation)",
        "image_only": "valid on the public DFU photograph set only — different population",
        "multimodal_image_plus_pressure": "invalid until paired sample_ids exist",
        "n_samples": str(len(y)),
    }
