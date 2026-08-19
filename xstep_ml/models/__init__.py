"""Model package. Optional CNN/fusion modules require torch (requirements-dl.txt)."""

from xstep_ml.models.gait import GAIT_CLASSES, gait_pipeline, zone_pipeline

__all__ = [
    "GAIT_CLASSES",
    "gait_pipeline",
    "zone_pipeline",
]
