"""Training loop with validation, early stopping, and checkpointing."""

from __future__ import annotations

import copy
import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader
from tqdm import tqdm

from xstep_ml.evaluation.metrics import compute_metrics
from xstep_ml.training.losses import OrdinalLoss, build_loss


@dataclass
class TrainConfig:
    max_epochs: int = 50
    lr: float = 1e-4
    weight_decay: float = 1e-4
    patience: int = 7
    loss: str = "cross_entropy"
    monitor: str = "macro_f1"
    num_classes: int = 4
    output_dir: str = "outputs"
    device: str = "auto"
    use_class_weights: bool = True
    label_names: list[str] = field(default_factory=list)


class Trainer:
    def __init__(
        self,
        model: nn.Module,
        config: TrainConfig,
        class_weights: torch.Tensor | None = None,
    ):
        self.config = config
        self.device = self._resolve_device(config.device)
        self.model = model.to(self.device)
        self.criterion = build_loss(config.loss, config.num_classes, class_weights)
        if hasattr(self.criterion, "weight") and self.criterion.weight is not None:
            self.criterion.weight = self.criterion.weight.to(self.device)
        if hasattr(self.criterion, "class_weight") and self.criterion.class_weight is not None:
            self.criterion.class_weight = self.criterion.class_weight.to(self.device)
        self.optimizer = AdamW(
            self.model.parameters(), lr=config.lr, weight_decay=config.weight_decay
        )
        self.scheduler: CosineAnnealingLR | None = None
        self.best_state: dict | None = None
        self.best_score = -np.inf
        self.history: list[dict] = []
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _resolve_device(device: str) -> torch.device:
        if device == "auto":
            if torch.cuda.is_available():
                return torch.device("cuda")
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return torch.device("mps")
            return torch.device("cpu")
        return torch.device(device)

    def fit(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
    ) -> dict:
        self.scheduler = CosineAnnealingLR(self.optimizer, T_max=self.config.max_epochs)
        epochs_without_improve = 0

        for epoch in range(1, self.config.max_epochs + 1):
            train_loss = self._train_epoch(train_loader)
            val_metrics = self.evaluate(val_loader)
            val_score = val_metrics[self.config.monitor]

            if self.scheduler:
                self.scheduler.step()

            record = {
                "epoch": epoch,
                "train_loss": train_loss,
                **{f"val_{k}": v for k, v in val_metrics.items()},
            }
            self.history.append(record)

            improved = val_score > self.best_score
            if improved:
                self.best_score = val_score
                self.best_state = copy.deepcopy(self.model.state_dict())
                epochs_without_improve = 0
                self._save_checkpoint("best_model.pt")
            else:
                epochs_without_improve += 1

            print(
                f"Epoch {epoch:03d} | loss={train_loss:.4f} | "
                f"val_{self.config.monitor}={val_score:.4f} | "
                f"val_acc={val_metrics['accuracy']:.4f}"
            )

            if epochs_without_improve >= self.config.patience:
                print(f"Early stopping at epoch {epoch}")
                break

        if self.best_state:
            self.model.load_state_dict(self.best_state)

        summary = {
            "best_score": self.best_score,
            "monitor": self.config.monitor,
            "epochs_run": len(self.history),
            "history": self.history,
        }
        with open(self.output_dir / "train_history.json", "w") as f:
            json.dump(summary, f, indent=2)
        return summary

    def _train_epoch(self, loader: DataLoader) -> float:
        self.model.train()
        total_loss = 0.0
        n = 0
        for images, labels in tqdm(loader, desc="train", leave=False):
            images = images.to(self.device)
            labels = labels.to(self.device)

            self.optimizer.zero_grad()
            outputs = self.model(images)
            if isinstance(self.criterion, OrdinalLoss):
                loss = self.criterion(outputs, labels)
            else:
                loss = self.criterion(outputs, labels)
            loss.backward()
            self.optimizer.step()

            total_loss += loss.item() * images.size(0)
            n += images.size(0)
        return total_loss / max(n, 1)

    @torch.no_grad()
    def evaluate(self, loader: DataLoader) -> dict:
        self.model.eval()
        all_preds: list[int] = []
        all_labels: list[int] = []
        all_probs: list[np.ndarray] = []

        for images, labels in loader:
            images = images.to(self.device)
            outputs = self.model(images)
            if isinstance(self.criterion, OrdinalLoss):
                preds = OrdinalLoss.predict(outputs).cpu().numpy()
                probs = torch.sigmoid(outputs[:, : self.config.num_classes - 1]).cpu().numpy()
            else:
                probs_t = torch.softmax(outputs, dim=1)
                preds = probs_t.argmax(dim=1).cpu().numpy()
                probs = probs_t.cpu().numpy()

            all_preds.extend(preds.tolist())
            all_labels.extend(labels.numpy().tolist())
            all_probs.extend(probs)

        return compute_metrics(
            np.array(all_labels),
            np.array(all_preds),
            np.array(all_probs) if all_probs else None,
            num_classes=self.config.num_classes,
            label_names=self.config.label_names or None,
        )

    def _save_checkpoint(self, filename: str) -> None:
        path = self.output_dir / filename
        torch.save(
            {
                "model_state_dict": self.model.state_dict(),
                "config": asdict(self.config),
                "best_score": self.best_score,
                "timestamp": time.time(),
            },
            path,
        )

    def predict_loader(self, loader: DataLoader) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        self.model.eval()
        preds, labels, probs = [], [], []
        with torch.no_grad():
            for images, y in loader:
                images = images.to(self.device)
                outputs = self.model(images)
                if isinstance(self.criterion, OrdinalLoss):
                    p = OrdinalLoss.predict(outputs).cpu().numpy()
                    pr = torch.sigmoid(outputs[:, : self.config.num_classes - 1]).cpu().numpy()
                else:
                    pr_t = torch.softmax(outputs, dim=1)
                    p = pr_t.argmax(dim=1).cpu().numpy()
                    pr = pr_t.cpu().numpy()
                preds.extend(p.tolist())
                labels.extend(y.numpy().tolist())
                probs.extend(pr)
        return np.array(labels), np.array(preds), np.array(probs)
