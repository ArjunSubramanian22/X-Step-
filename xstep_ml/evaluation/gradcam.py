"""Grad-CAM interpretability for CNN / transfer-learning models."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from torchvision import transforms as T


class GradCAM:
    def __init__(self, model: nn.Module, target_layer: nn.Module):
        self.model = model
        self.target_layer = target_layer
        self.activations: torch.Tensor | None = None
        self.gradients: torch.Tensor | None = None
        self._hooks = [
            target_layer.register_forward_hook(self._forward_hook),
            target_layer.register_full_backward_hook(self._backward_hook),
        ]

    def _forward_hook(self, _module, _inp, output):
        self.activations = output.detach()

    def _backward_hook(self, _module, _gin, grad_out):
        self.gradients = grad_out[0].detach()

    def remove_hooks(self):
        for h in self._hooks:
            h.remove()

    def __call__(self, x: torch.Tensor, class_idx: int | None = None) -> np.ndarray:
        self.model.zero_grad()
        logits = self.model(x)
        if class_idx is None:
            class_idx = int(logits.argmax(dim=1).item())
        score = logits[:, class_idx].sum()
        score.backward()

        assert self.gradients is not None and self.activations is not None
        weights = self.gradients.mean(dim=(2, 3), keepdim=True)
        cam = torch.relu((weights * self.activations).sum(dim=1, keepdim=True))
        cam = torch.nn.functional.interpolate(cam, size=x.shape[2:], mode="bilinear", align_corners=False)
        cam = cam.squeeze().cpu().numpy()
        cam = (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)
        return cam


def resolve_target_layer(model: nn.Module) -> nn.Module:
    """Pick a reasonable conv/feature layer for Grad-CAM."""
    if hasattr(model, "model") and hasattr(model.model, "layer4"):
        return model.model.layer4
    if hasattr(model, "model") and hasattr(model.model, "features"):
        return model.model.features[-1]
    if hasattr(model, "conv2"):
        return model.conv2
    raise ValueError("Could not resolve target layer for Grad-CAM")


def generate_gradcam_batch(
    model: nn.Module,
    image_paths: list[str],
    output_dir: Path | str,
    device: torch.device | str = "cpu",
    image_size: int = 224,
    max_images: int = 8,
) -> list[str]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    model = model.to(device)
    model.eval()
    target_layer = resolve_target_layer(model)
    gradcam = GradCAM(model, target_layer)

    transform = T.Compose([
        T.Resize((image_size, image_size)),
        T.ToTensor(),
        T.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
    ])

    saved: list[str] = []
    for path in image_paths[:max_images]:
        img_pil = Image.open(path).convert("RGB")
        x = transform(img_pil).unsqueeze(0).to(device)
        x.requires_grad_(True)

        cam = gradcam(x)
        rgb = np.array(img_pil.resize((image_size, image_size))) / 255.0

        fig, axes = plt.subplots(1, 2, figsize=(8, 4))
        axes[0].imshow(rgb)
        axes[0].set_title("Original")
        axes[0].axis("off")
        axes[1].imshow(rgb)
        axes[1].imshow(cam, cmap="jet", alpha=0.45)
        axes[1].set_title("Grad-CAM")
        axes[1].axis("off")
        out = output_dir / f"gradcam_{Path(path).stem}.png"
        fig.tight_layout()
        fig.savefig(out, dpi=150)
        plt.close(fig)
        saved.append(str(out))

    gradcam.remove_hooks()
    return saved
