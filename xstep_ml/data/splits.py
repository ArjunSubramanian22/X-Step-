"""Leakage-safe splitting by Roboflow source image ID."""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Iterable

import numpy as np
from sklearn.model_selection import StratifiedKFold, train_test_split

_SOURCE_RE = re.compile(r"^(.+)_jpg\.rf\.")


def extract_source_id(filename: str) -> str:
    """Return the Roboflow source-image group id for an augmented filename."""
    match = _SOURCE_RE.match(filename)
    if match:
        return match.group(1)
    stem = Path(filename).stem
    if ".rf." in stem:
        return stem.split(".rf.")[0]
    return stem


def _indices_for_groups(groups: dict[str, list[int]], group_list: list[str]) -> np.ndarray:
    out: list[int] = []
    for g in group_list:
        out.extend(groups[g])
    return np.array(out, dtype=np.int64)


def groupwise_split_indices(
    source_ids: Iterable[str],
    labels: Iterable[int],
    test_size: float = 0.15,
    val_size: float = 0.15,
    random_state: int = 67,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Split indices by source image so augmented siblings never cross splits.
    Returns train_idx, val_idx, test_idx.
    """
    source_ids = list(source_ids)
    labels = list(labels)

    groups: dict[str, list[int]] = defaultdict(list)
    group_label: dict[str, int] = {}
    for idx, (src, label) in enumerate(zip(source_ids, labels)):
        groups[src].append(idx)
        group_label[src] = label

    unique_groups = list(groups.keys())
    group_labels = [group_label[g] for g in unique_groups]

    if test_size > 0:
        g_trainval, g_test, _, _ = train_test_split(
            unique_groups,
            group_labels,
            test_size=test_size,
            random_state=random_state,
            stratify=group_labels,
        )
    else:
        g_trainval, g_test = unique_groups, []

    trainval_labels = [group_label[g] for g in g_trainval]
    if val_size > 0 and len(g_trainval) > 1:
        g_train, g_val, _, _ = train_test_split(
            g_trainval,
            trainval_labels,
            test_size=val_size / (1 - test_size) if test_size < 1 else val_size,
            random_state=random_state,
            stratify=trainval_labels,
        )
    else:
        g_train, g_val = g_trainval, []

    return (
        _indices_for_groups(groups, g_train),
        _indices_for_groups(groups, g_val),
        _indices_for_groups(groups, g_test),
    )


def load_ulcer_manifest(archive_root: Path) -> tuple[list[str], list[int], list[str]]:
    """Load (path, label, source_id) for all images in train/valid/test."""
    samples: list[tuple[str, int, str]] = []
    for split in ("train", "valid", "test"):
        split_dir = archive_root / split
        if not split_dir.is_dir():
            continue
        for grade_dir in sorted(split_dir.iterdir()):
            if not grade_dir.is_dir():
                continue
            label = int(grade_dir.name.split()[-1]) - 1
            for img_path in grade_dir.iterdir():
                if img_path.suffix.lower() in {".jpg", ".jpeg", ".png"}:
                    samples.append((str(img_path), label, extract_source_id(img_path.name)))
    paths = [s[0] for s in samples]
    labels = [s[1] for s in samples]
    source_ids = [s[2] for s in samples]
    return paths, labels, source_ids


def _sources_in_multiple_roboflow_splits(paths: list[str], source_ids: list[str]) -> int:
    by_src: dict[str, set[str]] = defaultdict(set)
    for path, src in zip(paths, source_ids):
        for split in ("train", "valid", "test"):
            if f"/{split}/" in path.replace("\\", "/"):
                by_src[src].add(split)
                break
    return sum(1 for splits in by_src.values() if len(splits) > 1)


def roboflow_preset_splits(archive_root: Path, val_fraction_from_train: float = 0.15):
    """
    Prefer Roboflow train/valid/test folders when source groups are disjoint.
    Falls back to full group-wise split if the export has cross-split sources.
    """
    by_split: dict[str, list[tuple[str, int, str]]] = {"train": [], "valid": [], "test": []}
    for split in by_split:
        split_dir = archive_root / split
        if not split_dir.is_dir():
            continue
        for grade_dir in sorted(split_dir.iterdir()):
            if not grade_dir.is_dir():
                continue
            label = int(grade_dir.name.split()[-1]) - 1
            for img_path in grade_dir.iterdir():
                if img_path.suffix.lower() in {".jpg", ".jpeg", ".png"}:
                    by_split[split].append((str(img_path), label, extract_source_id(img_path.name)))

    ordered = by_split["train"] + by_split["valid"] + by_split["test"]
    all_paths = [s[0] for s in ordered]
    all_labels = [s[1] for s in ordered]
    all_sources = [s[2] for s in ordered]

    if _sources_in_multiple_roboflow_splits(all_paths, all_sources) > 0:
        train_idx, val_idx, test_idx = groupwise_split_indices(
            all_sources, all_labels, test_size=0.15, val_size=0.15, random_state=67
        )
        return all_paths, all_labels, {
            "train_fit": train_idx,
            "val_fit": val_idx,
            "eval_valid": val_idx,
            "eval_test": test_idx,
            "split_strategy": "groupwise_fallback",
        }

    indices: dict[str, np.ndarray] = {}
    offset = 0
    for split in ("train", "valid", "test"):
        n = len(by_split[split])
        indices[split] = np.arange(offset, offset + n, dtype=np.int64)
        offset += n

    train_samples = by_split["train"]
    if train_samples and val_fraction_from_train > 0:
        src_ids = [s[2] for s in train_samples]
        labs = [s[1] for s in train_samples]
        tr_local, va_local, _ = groupwise_split_indices(
            src_ids, labs, test_size=0.0, val_size=val_fraction_from_train, random_state=67
        )
        indices["train_fit"] = indices["train"][tr_local]
        indices["val_fit"] = indices["train"][va_local]
    else:
        indices["train_fit"] = indices["train"]
        indices["val_fit"] = indices["valid"]

    indices["eval_valid"] = indices["valid"]
    indices["eval_test"] = indices["test"]
    indices["split_strategy"] = "roboflow_folders"
    return all_paths, all_labels, indices


def stratified_group_kfold(
    source_ids: list[str],
    labels: list[int],
    n_splits: int = 5,
    random_state: int = 67,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """K-fold CV where folds are defined at the source-image group level."""
    groups: dict[str, list[int]] = defaultdict(list)
    group_label: dict[str, int] = {}
    for idx, (src, label) in enumerate(zip(source_ids, labels)):
        groups[src].append(idx)
        group_label[src] = label

    unique_groups = list(groups.keys())
    group_labels = [group_label[g] for g in unique_groups]

    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    folds: list[tuple[np.ndarray, np.ndarray]] = []
    for train_g_idx, val_g_idx in skf.split(unique_groups, group_labels):
        train_groups = [unique_groups[i] for i in train_g_idx]
        val_groups = [unique_groups[i] for i in val_g_idx]
        train_idx = _indices_for_groups(groups, train_groups)
        val_idx = _indices_for_groups(groups, val_groups)
        folds.append((train_idx, val_idx))
    return folds
