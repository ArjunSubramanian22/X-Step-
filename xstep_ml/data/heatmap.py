"""Pressure heatmap dataset loading and dataloaders."""

from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset, Subset
from torchvision import transforms as T

from xstep_ml.config import DEFAULT_BATCH_SIZE
from xstep_ml.data.splits import groupwise_split_indices, stratified_group_kfold


def load_heatmap_arrays(data_path: Path | str | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Load X, y from Kaggle pickle files. Downloads via kagglehub if path not given."""
    if data_path is None:
        import kagglehub

        data_path = kagglehub.dataset_download("mahdiislam/pressure-sensor-heatmaprgb")

    data_path = Path(data_path)
    with open(data_path / "X_9_RGB.pickle", "rb") as f:
        x = pickle.load(f)
    with open(data_path / "y_9_RGB.pickle", "rb") as f:
        y = pickle.load(f)
    return np.asarray(x), np.asarray(y)


def heatmap_train_transforms() -> T.Compose:
    return T.Compose([
        T.RandomHorizontalFlip(),
        T.RandomAffine(degrees=10, translate=(0.05, 0.05), scale=(0.95, 1.05)),
        T.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
    ])


def heatmap_eval_transforms() -> T.Compose:
    return T.Compose([
        T.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
    ])


class HeatmapDataset(Dataset):
    def __init__(self, x: torch.Tensor, y: torch.Tensor, transform: T.Compose | None = None):
        self.x = x
        self.y = y
        self.transform = transform

    def __len__(self) -> int:
        return len(self.x)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, int]:
        img = self.x[idx]
        if self.transform:
            img = self.transform(img)
        return img, int(self.y[idx])


def _prepare_tensors(x: np.ndarray, y: np.ndarray) -> tuple[torch.Tensor, torch.Tensor]:
    x_t = torch.tensor(x, dtype=torch.float32).permute(0, 3, 1, 2)
    y_t = torch.tensor(y, dtype=torch.int64)
    return x_t, y_t


def build_heatmap_dataloaders(
    data_path: Path | str | None = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
    test_size: float = 0.2,
    val_size: float = 0.15,
    random_state: int = 67,
    num_workers: int = 0,
) -> tuple[DataLoader, DataLoader, DataLoader, dict]:
    x, y = load_heatmap_arrays(data_path)
    x_t, y_t = _prepare_tensors(x, y)

    # Each sample is independent in this pickle dataset (no augmentation siblings)
    n = len(y_t)
    indices = np.arange(n)
    pseudo_sources = [str(i) for i in indices]
    train_idx, val_idx, test_idx = groupwise_split_indices(
        pseudo_sources, y_t.tolist(), test_size=test_size, val_size=val_size, random_state=random_state
    )

    train_base = HeatmapDataset(x_t, y_t, transform=heatmap_train_transforms())
    eval_base = HeatmapDataset(x_t, y_t, transform=heatmap_eval_transforms())

    loaders = {
        "train": DataLoader(
            Subset(train_base, train_idx.tolist()),
            batch_size=batch_size,
            shuffle=True,
            num_workers=num_workers,
        ),
        "val": DataLoader(
            Subset(eval_base, val_idx.tolist()),
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
        ),
        "test": DataLoader(
            Subset(eval_base, test_idx.tolist()),
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
        ),
    }
    meta = {"x": x_t, "y": y_t, "indices": {"train": train_idx, "val": val_idx, "test": test_idx}}
    return loaders["train"], loaders["val"], loaders["test"], meta


def build_heatmap_kfold_loaders(
    data_path: Path | str | None = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
    n_splits: int = 5,
    random_state: int = 67,
) -> list[tuple[DataLoader, DataLoader, dict]]:
    x, y = load_heatmap_arrays(data_path)
    x_t, y_t = _prepare_tensors(x, y)
    pseudo_sources = [str(i) for i in range(len(y_t))]
    folds = stratified_group_kfold(pseudo_sources, y_t.tolist(), n_splits=n_splits, random_state=random_state)

    fold_loaders = []
    for train_idx, val_idx in folds:
        train_base = HeatmapDataset(x_t, y_t, transform=heatmap_train_transforms())
        eval_base = HeatmapDataset(x_t, y_t, transform=heatmap_eval_transforms())
        train_loader = DataLoader(
            Subset(train_base, train_idx.tolist()), batch_size=batch_size, shuffle=True
        )
        val_loader = DataLoader(
            Subset(eval_base, val_idx.tolist()), batch_size=batch_size, shuffle=False
        )
        fold_loaders.append((train_loader, val_loader, {"train": train_idx, "val": val_idx}))
    return fold_loaders
