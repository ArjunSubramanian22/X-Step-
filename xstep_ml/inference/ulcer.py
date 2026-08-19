"""Ulcer photo inference wrapper (on-device API)."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from xstep_ml.config import ULCER_GRADES, ULCER_NUM_CLASSES

_IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
_IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


class UlcerImagePredictor:
    def __init__(self, weights_path: Path | None = None, image_size: int = 64):
        self.image_size = image_size
        self.model = None
        self.device = "cpu"
        self.grades = list(ULCER_GRADES)
        try:
            import torch

            from xstep_ml.models.ulcer import UlcerNN

            self.torch = torch
            self.device = "cpu"
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                self.device = "mps"
            model = UlcerNN(num_classes=ULCER_NUM_CLASSES)
            path = weights_path or Path("ulcer model/ulcer_model_state.pth")
            if path.exists():
                state = torch.load(path, map_location="cpu")
                if isinstance(state, dict) and "model_state_dict" in state:
                    state = state["model_state_dict"]
                model.load_state_dict(state)
            model.eval()
            self.model = model.to(self.device)
        except Exception:
            self.model = None

    def predict(self, image_bytes: bytes) -> dict:
        from io import BytesIO

        from PIL import Image

        img = Image.open(BytesIO(image_bytes)).convert("RGB").resize((self.image_size, self.image_size))
        arr = np.asarray(img, dtype=np.float32) / 255.0
        if self.model is None:
            # Color heuristic fallback when weights are unavailable.
            red = float(arr[:, :, 0].mean())
            sat = float(arr.std())
            grade = int(np.clip(round(red * 3 + sat * 2), 0, 3))
            probs = np.zeros(4, dtype=np.float64)
            probs[grade] = 0.55
            probs += 0.15
            probs /= probs.sum()
            return {
                "grade": int(grade + 1),
                "label": self.grades[grade],
                "probs": probs.tolist(),
                "backend": "heuristic",
                "disclaimer": "Not a diagnosis. Confirm with a clinician.",
            }

        tensor = (arr - _IMAGENET_MEAN) / _IMAGENET_STD
        tensor = tensor.transpose(2, 0, 1)
        t = self.torch.from_numpy(tensor).unsqueeze(0).to(self.device)
        with self.torch.no_grad():
            logits = self.model(t)
            probs = self.torch.softmax(logits, dim=1).cpu().numpy()[0]
        grade = int(np.argmax(probs))
        return {
            "grade": int(grade + 1),
            "label": self.grades[grade],
            "probs": [float(p) for p in probs],
            "backend": "ulcer_cnn",
            "disclaimer": "Not a diagnosis. Confirm with a clinician.",
        }
