#!/usr/bin/env python3
"""Smoke-test the production API locally."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from xstep_ml.data.synthetic_gait import synthesize_window
from xstep_ml.inference.engine import ProductionEngine
from xstep_ml.models.clinical import ClinicalProfile


def main() -> None:
    rng = np.random.default_rng(7)
    frames, label, zone = synthesize_window("left_forefoot_overload", rng)
    engine = ProductionEngine()
    result = engine.analyze_window(
        frames.tolist(),
        profile=ClinicalProfile(neuropathy="Moderate", hba1c=8.1, prior_ulcer=False),
    )
    print(json.dumps({
        "injected_label": label,
        "injected_zone": zone,
        "predicted_gait": result.gait_pattern,
        "predicted_zone": result.high_risk_zone,
        "health_index": round(result.health_index, 2),
        "level": result.level,
        "alerts": len(result.alerts),
        "peak_kpa": round(result.extras.get("peak_any", 0), 1),
    }, indent=2))


if __name__ == "__main__":
    main()
