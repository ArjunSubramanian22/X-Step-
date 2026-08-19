"""Pressure-window gait pattern and high-risk-zone models."""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from xstep_ml.config import ROOT

GAIT_CLASSES = (
    "normal",
    "left_forefoot_overload",
    "right_forefoot_overload",
    "left_heel_overload",
    "right_heel_overload",
    "left_lateral_overload",
    "right_lateral_overload",
    "asymmetric_antalgic",
    "shuffling_low_cadence",
)

ZONE_CLASSES = ("met1", "met2", "met5", "heel", "none")

ARTIFACT_DIR = ROOT / "artifacts"


def gait_pipeline() -> Pipeline:
    """Selected production model: L2 logistic regression (see EHB grouped-CV table)."""
    return Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "clf",
                LogisticRegression(
                    max_iter=400,
                    class_weight="balanced",
                    random_state=67,
                ),
            ),
        ]
    )


def zone_pipeline() -> Pipeline:
    return Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "clf",
                GradientBoostingClassifier(
                    n_estimators=120,
                    max_depth=3,
                    learning_rate=0.08,
                    random_state=67,
                ),
            ),
        ]
    )


def save_artifact(model: object, name: str) -> Path:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    path = ARTIFACT_DIR / name
    joblib.dump(model, path)
    return path


def load_artifact(name: str):
    path = ARTIFACT_DIR / name
    if not path.exists():
        raise FileNotFoundError(path)
    return joblib.load(path)
