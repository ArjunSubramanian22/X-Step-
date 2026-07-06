"""Late-fusion model combining heatmap and ulcer image embeddings."""

from __future__ import annotations

import torch
import torch.nn as nn

from xstep_ml.models.heatmap import build_heatmap_model
from xstep_ml.models.ulcer import build_ulcer_model


class MultimodalFusionModel(nn.Module):
    """
    Dual-branch late fusion: pretrained backbones produce embeddings,
    concatenated and passed through a fusion head for joint risk scoring.
    """

    def __init__(
        self,
        heatmap_backbone: str = "resnet50",
        ulcer_backbone: str = "efficientnet_b0",
        num_ulcer_classes: int = 4,
        num_heatmap_classes: int = 9,
        fusion_hidden: int = 128,
        dropout: float = 0.3,
        pretrained: bool = True,
        task: str = "ulcer",  # 'ulcer' | 'heatmap' | 'multitask'
    ):
        super().__init__()
        self.task = task
        self.heatmap_encoder = build_heatmap_model(heatmap_backbone, num_heatmap_classes, pretrained, dropout)
        self.ulcer_encoder = build_ulcer_model(ulcer_backbone, num_ulcer_classes, pretrained, dropout)

        heat_dim = self._embedding_dim(self.heatmap_encoder, heatmap_backbone)
        ulcer_dim = self._embedding_dim(self.ulcer_encoder, ulcer_backbone)

        if task == "ulcer":
            self.fusion = nn.Sequential(
                nn.Linear(heat_dim + ulcer_dim, fusion_hidden),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(fusion_hidden, num_ulcer_classes),
            )
        elif task == "heatmap":
            self.fusion = nn.Sequential(
                nn.Linear(heat_dim + ulcer_dim, fusion_hidden),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(fusion_hidden, num_heatmap_classes),
            )
        else:
            self.fusion_ulcer = nn.Sequential(
                nn.Linear(heat_dim + ulcer_dim, fusion_hidden),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(fusion_hidden, num_ulcer_classes),
            )
            self.fusion_heatmap = nn.Sequential(
                nn.Linear(heat_dim + ulcer_dim, fusion_hidden),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(fusion_hidden, num_heatmap_classes),
            )

    @staticmethod
    def _embedding_dim(model: nn.Module, backbone: str) -> int:
        if backbone == "heat_cnn":
            return 16
        if backbone == "ulcer_cnn":
            return 16
        if backbone == "resnet50":
            return 2048
        if backbone == "efficientnet_b0":
            return 1280
        raise ValueError(backbone)

    def _encode_heatmap(self, x: torch.Tensor) -> torch.Tensor:
        enc = self.heatmap_encoder
        if hasattr(enc, "forward_features"):
            return enc.forward_features(x)
        if hasattr(enc, "model"):
            m = enc.model
            x = m.conv1(x)
            x = m.bn1(x)
            x = m.relu(x)
            x = m.maxpool(x)
            x = m.layer1(x)
            x = m.layer2(x)
            x = m.layer3(x)
            x = m.layer4(x)
            x = m.avgpool(x)
            return torch.flatten(x, 1)
        out = enc(x)
        return out

    def _encode_ulcer(self, x: torch.Tensor) -> torch.Tensor:
        enc = self.ulcer_encoder
        if hasattr(enc, "forward_features"):
            return enc.forward_features(x)
        return enc(x)

    def forward(
        self,
        heatmap: torch.Tensor,
        ulcer_image: torch.Tensor,
    ) -> torch.Tensor | tuple[torch.Tensor, torch.Tensor]:
        h = self._encode_heatmap(heatmap)
        u = self._encode_ulcer(ulcer_image)
        fused = torch.cat([h, u], dim=1)

        if self.task == "ulcer":
            return self.fusion(fused)
        if self.task == "heatmap":
            return self.fusion(fused)
        return self.fusion_ulcer(fused), self.fusion_heatmap(fused)
