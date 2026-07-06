"""Pressure heatmap posture classifier."""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models

from xstep_ml.config import HEATMAP_NUM_CLASSES


class HeatCNN(nn.Module):
    """Original small CNN for 224x224 heatmaps."""

    def __init__(self, num_classes: int = HEATMAP_NUM_CLASSES):
        super().__init__()
        self.conv1 = nn.Conv2d(3, 32, 3)
        self.pool = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(32, 64, 3)
        self.fc1 = nn.Linear(64 * 54 * 54, 32)
        self.fc2 = nn.Linear(32, 16)
        self.out = nn.Linear(16, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = x.flatten(1)
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        return self.out(x)


class HeatmapTransferBackbone(nn.Module):
    def __init__(
        self,
        backbone: str = "resnet50",
        num_classes: int = HEATMAP_NUM_CLASSES,
        dropout: float = 0.3,
        pretrained: bool = True,
    ):
        super().__init__()
        weights = "DEFAULT" if pretrained else None
        if backbone == "resnet50":
            net = models.resnet50(weights=weights)
            in_features = net.fc.in_features
            net.fc = nn.Sequential(nn.Dropout(dropout), nn.Linear(in_features, num_classes))
            self.model = net
        elif backbone == "efficientnet_b0":
            net = models.efficientnet_b0(weights=weights)
            in_features = net.classifier[1].in_features
            net.classifier = nn.Sequential(nn.Dropout(dropout), nn.Linear(in_features, num_classes))
            self.model = net
        else:
            raise ValueError(f"Unknown backbone: {backbone}")
        self.backbone_name = backbone

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.model(x)


def build_heatmap_model(
    architecture: str = "heat_cnn",
    num_classes: int = HEATMAP_NUM_CLASSES,
    pretrained: bool = True,
    dropout: float = 0.3,
) -> nn.Module:
    if architecture == "heat_cnn":
        return HeatCNN(num_classes=num_classes)
    if architecture in ("resnet50", "efficientnet_b0"):
        return HeatmapTransferBackbone(
            backbone=architecture,
            num_classes=num_classes,
            dropout=dropout,
            pretrained=pretrained,
        )
    raise ValueError(f"Unknown architecture: {architecture}")
