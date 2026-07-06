"""Classification losses including ordinal and focal variants."""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class FocalLoss(nn.Module):
    def __init__(self, gamma: float = 2.0, weight: torch.Tensor | None = None):
        super().__init__()
        self.gamma = gamma
        self.weight = weight

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        ce = F.cross_entropy(logits, targets, weight=self.weight, reduction="none")
        pt = torch.exp(-ce)
        return ((1 - pt) ** self.gamma * ce).mean()


class OrdinalLoss(nn.Module):
    """
    CORAL-style ordinal loss for ordered grades (e.g. DFU 1-4).
    Treats K classes as K-1 binary thresholds.
    """

    def __init__(self, num_classes: int, weight: torch.Tensor | None = None):
        super().__init__()
        self.num_classes = num_classes
        self.num_thresholds = num_classes - 1
        self.bce = nn.BCEWithLogitsLoss(reduction="none")
        self.class_weight = weight

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        # logits shape: (B, num_classes) — use first K-1 dims as thresholds
        thresholds = logits[:, : self.num_thresholds]
        levels = torch.zeros_like(thresholds)
        for i in range(self.num_thresholds):
            levels[:, i] = (targets > i).float()
        loss = self.bce(thresholds, levels).mean(dim=1)
        if self.class_weight is not None:
            loss = loss * self.class_weight[targets]
        return loss.mean()

    @staticmethod
    def predict(logits: torch.Tensor) -> torch.Tensor:
        probs = torch.sigmoid(logits[:, :-1])
        return (probs > 0.5).sum(dim=1)


def build_loss(
    loss_name: str,
    num_classes: int = 4,
    class_weights: torch.Tensor | None = None,
) -> nn.Module:
    if loss_name == "cross_entropy":
        return nn.CrossEntropyLoss(weight=class_weights)
    if loss_name == "focal":
        return FocalLoss(weight=class_weights)
    if loss_name == "ordinal":
        return OrdinalLoss(num_classes=num_classes, weight=class_weights)
    raise ValueError(f"Unknown loss: {loss_name}")
