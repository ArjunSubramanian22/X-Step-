"""Ulcer wound-image dataset with proper train/eval transforms."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch.utils.data import DataLoader, Dataset, Subset
from torchvision import transforms as T

from xstep_ml.config import DEFAULT_BATCH_SIZE, DEFAULT_IMAGE_SIZE, ULCER_ARCHIVE
from xstep_ml.data.splits import load_ulcer_manifest, roboflow_preset_splits


def ulcer_train_transforms(image_size: int = DEFAULT_IMAGE_SIZE) -> T.Compose:
    return T.Compose([
        T.Resize((image_size, image_size)),
        T.RandomHorizontalFlip(),
        T.RandomRotation(15),
        T.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.1),
        T.ToTensor(),
        T.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
    ])


def ulcer_eval_transforms(image_size: int = DEFAULT_IMAGE_SIZE) -> T.Compose:
    return T.Compose([
        T.Resize((image_size, image_size)),
        T.ToTensor(),
        T.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
    ])


class UlcerImageDataset(Dataset):
    """Loads images on demand; augmentation applied per __getitem__ when training."""

    def __init__(
        self,
        image_paths: list[str],
        labels: list[int],
        transform: T.Compose | None = None,
    ):
        self.image_paths = image_paths
        self.labels = labels
        self.transform = transform

    def __len__(self) -> int:
        return len(self.image_paths)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, int]:
        img = Image.open(self.image_paths[idx]).convert("RGB")
        if self.transform:
            img = self.transform(img)
        return img, self.labels[idx]


def build_ulcer_dataloaders(
    archive_root: Path | None = None,
    image_size: int = DEFAULT_IMAGE_SIZE,
    batch_size: int = DEFAULT_BATCH_SIZE,
    num_workers: int = 0,
    split_mode: str = "groupwise",
) -> tuple[DataLoader, DataLoader, DataLoader, DataLoader, dict, dict]:
    """
    Returns train, val (early-stop), roboflow-valid, test loaders plus split metadata.
    split_mode: 'groupwise' (default, leakage-safe) or 'roboflow' (uses folders with fallback).
    """
    archive_root = archive_root or ULCER_ARCHIVE
    paths, labels, source_ids = load_ulcer_manifest(archive_root)

    if split_mode == "roboflow":
        _, _, indices = roboflow_preset_splits(archive_root)
        train_idx = indices["train_fit"]
        val_idx = indices["val_fit"]
        rf_valid_idx = indices["eval_valid"]
        test_idx = indices["eval_test"]
        split_strategy = indices.get("split_strategy", "roboflow")
    else:
        from xstep_ml.data.splits import groupwise_split_indices

        train_idx, val_idx, test_idx = groupwise_split_indices(source_ids, labels)
        rf_valid_idx = val_idx
        split_strategy = "groupwise"

    full_eval = UlcerImageDataset(paths, labels, transform=ulcer_eval_transforms(image_size))
    train_ds = UlcerImageDataset(paths, labels, transform=ulcer_train_transforms(image_size))

    loaders = {
        "train": DataLoader(
            Subset(train_ds, train_idx.tolist()),
            batch_size=batch_size,
            shuffle=True,
            num_workers=num_workers,
            pin_memory=torch.cuda.is_available(),
        ),
        "val": DataLoader(
            Subset(full_eval, val_idx.tolist()),
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
        ),
        "roboflow_valid": DataLoader(
            Subset(full_eval, rf_valid_idx.tolist()),
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
        ),
        "test": DataLoader(
            Subset(full_eval, test_idx.tolist()),
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
        ),
    }
    meta = {
        "paths": paths,
        "labels": labels,
        "source_ids": source_ids,
        "split_strategy": split_strategy,
        "indices": {
            "train": train_idx,
            "val": val_idx,
            "roboflow_valid": rf_valid_idx,
            "test": test_idx,
        },
    }
    return loaders["train"], loaders["val"], loaders["roboflow_valid"], loaders["test"], loaders, meta


def compute_class_weights(labels: list[int], num_classes: int = 4) -> torch.Tensor:
    counts = np.bincount(labels, minlength=num_classes).astype(np.float64)
    counts = np.maximum(counts, 1.0)
    weights = counts.sum() / (num_classes * counts)
    return torch.tensor(weights, dtype=torch.float32)
