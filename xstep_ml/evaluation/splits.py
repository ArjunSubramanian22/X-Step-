"""Leakage-safe subject/session splits for pressure windows."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

import numpy as np
from sklearn.model_selection import GroupKFold, GroupShuffleSplit, LeaveOneGroupOut


class LeakageError(AssertionError):
    """Raised when the same grouping identifier appears in train and test."""


def overlapping_ids(train_ids: Iterable, test_ids: Iterable) -> set:
    return set(map(_canon, train_ids)) & set(map(_canon, test_ids))


def _canon(x) -> str:
    return str(x)


def assert_no_group_overlap(train_ids: Iterable, test_ids: Iterable, *, kind: str = "group") -> None:
    overlap = overlapping_ids(train_ids, test_ids)
    if overlap:
        sample = sorted(overlap)[:12]
        raise LeakageError(
            f"{kind} identifiers overlap train/test: {sample} "
            f"({len(overlap)} overlapping ids). Use subject- or session-grouped splits."
        )


def grouped_train_test_split(
    X: np.ndarray,
    y: np.ndarray,
    groups: np.ndarray,
    *,
    test_size: float = 0.2,
    random_state: int = 67,
    kind: str = "subject",
) -> tuple[np.ndarray, np.ndarray]:
    """Hold out entire groups. Fails if leakage is detected."""
    gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    train_idx, test_idx = next(gss.split(X, y, groups))
    assert_no_group_overlap(groups[train_idx], groups[test_idx], kind=kind)
    return train_idx, test_idx


def group_kfold_indices(
    X: np.ndarray,
    y: np.ndarray,
    groups: np.ndarray,
    *,
    n_splits: int = 5,
    kind: str = "subject",
) -> list[tuple[np.ndarray, np.ndarray]]:
    n_groups = len(np.unique(groups))
    splits = min(n_splits, n_groups)
    if splits < 2:
        raise ValueError("need at least 2 groups for grouped CV")
    gkf = GroupKFold(n_splits=splits)
    folds: list[tuple[np.ndarray, np.ndarray]] = []
    for train_idx, test_idx in gkf.split(X, y, groups):
        assert_no_group_overlap(groups[train_idx], groups[test_idx], kind=kind)
        folds.append((train_idx, test_idx))
    return folds


def leave_one_subject_out(groups: np.ndarray) -> list[tuple[np.ndarray, np.ndarray]]:
    logo = LeaveOneGroupOut()
    dummy = np.zeros(len(groups))
    folds = []
    for train_idx, test_idx in logo.split(dummy, dummy, groups):
        assert_no_group_overlap(groups[train_idx], groups[test_idx], kind="subject")
        folds.append((train_idx, test_idx))
    return folds


def session_ids_from_subject_and_bout(subject_id: Sequence, bout_id: Sequence) -> np.ndarray:
    return np.array([f"{int(s)}::{int(b)}" for s, b in zip(subject_id, bout_id)], dtype=object)
