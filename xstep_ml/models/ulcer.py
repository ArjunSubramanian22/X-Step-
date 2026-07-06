"""Ulcer wound grading models: baseline CNN and transfer-learning backbones."""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models

from xstep_ml.config import ULCER_NUM_CLASSES


class UlcerNN(nn.Module):
    """Original small CNN (64x64). Kept for baseline comparison."""

    def __init__(self, num_classes: int = ULCER_NUM_CLASSES):
        super().__init__()
        self.conv1 = nn.Conv2d(3, 32, 3)
        self.pool = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(32, 64, 3)
        self.fc1 = nn.Linear(64 * 14 * 14, 32)
        self.fc2 = nn.Linear(32, 16)
        self.out = nn.Linear(16, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = x.flatten(1)
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        return self.out(x)


class TransferBackbone(nn.Module):
    """Pretrained backbone with replaced classification head."""

    def __init__(
        self,
        backbone: str = "efficientnet_b0",
        num_classes: int = ULCER_NUM_CLASSES,
        dropout: float = 0.3,
        pretrained: bool = True,
    ):
        super().__init__()
        self.backbone_name = backbone
        weights = "DEFAULT" if pretrained else None

        if backbone == "resnet50":
            net = models.resnet50(weights=weights)
            in_features = net.fc.in_features
            net.fc = nn.Sequential(
                nn.Dropout(dropout),
                nn.Linear(in_features, num_classes),
            )
            self.model = net
            self.features = nn.Sequential(*list(net.children())[:-1])
            self.classifier = net.fc
        elif backbone == "efficientnet_b0":
            net = models.efficientnet_b0(weights=weights)
            in_features = net.classifier[1].in_features
            net.classifier = nn.Sequential(
                nn.Dropout(dropout),
                nn.Linear(in_features, num_classes),
            )
            self.model = net
            self.features = net.features
            self.classifier = net.classifier
        else:
            raise ValueError(f"Unknown backbone: {backbone}")

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.model(x)

    def forward_features(self, x: torch.Tensor) -> torch.Tensor:
        if self.backbone_name == "resnet50":
            x = self.model.conv1(x)
            x = self.model.bn1(x)
            x = self.model.relu(x)
            x = self.model.maxpool(x)
            x = self.model.layer1(x)
            x = self.model.layer2(x)
            x = self.model.layer3(x)
            x = self.model.layer4(x)
            x = self.model.avgpool(x)
            return torch.flatten(x, 1)
        x = self.features(x)
        x = self.model.avgpool(x)
        return torch.flatten(x, 1)


def build_ulcer_model(
    architecture: str = "efficientnet_b0",
    num_classes: int = ULCER_NUM_CLASSES,
    pretrained: bool = True,
    dropout: float = 0.3,
) -> nn.Module:
    """
    architecture: 'ulcer_cnn' | 'resnet50' | 'efficientnet_b0'
    """
    if architecture == "ulcer_cnn":
        return UlcerNN(num_classes=num_classes)
    if architecture in ("resnet50", "efficientnet_b0"):
        return TransferBackbone(
            backbone=architecture,
            num_classes=num_classes,
            dropout=dropout,
            pretrained=pretrained,
        )
    raise ValueError(f"Unknown architecture: {architecture}")
