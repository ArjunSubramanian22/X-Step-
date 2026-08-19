"""Production inference: gait, high-risk zone, clinical fusion, ulcer image."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from xstep_ml.biomechanics import GaitWindow, extract_features
from xstep_ml.config import ARTIFACT_DIR, GAIT_MODEL_NAME, ZONE_MODEL_NAME
from xstep_ml.hardware import ALERT_PRESSURE_KPA, HIGH_RISK_PEAK_KPA, SITE_TO_APP_ZONE, SensorSite
from xstep_ml.inference.explain import contributions_as_dicts
from xstep_ml.models.clinical import ClinicalProfile, clinical_risk_score, iwgdf_risk_category
from xstep_ml.models.gait import load_artifact


@dataclass
class PressureAlert:
    foot: str
    site: str
    zone: str
    value_kpa: float
    threshold_kpa: float
    message: str


@dataclass
class RiskResult:
    health_index: float
    level: str
    gait_pattern: str
    gait_confidence: float
    high_risk_zone: str
    zone_confidence: float
    iwgdf_category: int
    factors: dict[str, float]
    alerts: list[PressureAlert]
    extras: dict[str, float]
    contributions: list[dict]


def _predict_label(model, x: np.ndarray) -> tuple[str, float]:
    """Return (label, confidence). Works across sklearn pickle versions."""
    if hasattr(model, "predict_proba"):
        try:
            proba = model.predict_proba(x)[0]
            idx = int(np.argmax(proba))
            return str(model.classes_[idx]), float(proba[idx])
        except Exception:
            pass
    pred = model.predict(x)[0]
    return str(pred), 1.0


def _level(score: float) -> str:
    if score < 35:
        return "green"
    if score < 65:
        return "amber"
    return "red"


class ProductionEngine:
    def __init__(self, artifact_dir: Path | None = None):
        self.artifact_dir = artifact_dir or ARTIFACT_DIR
        self.gait_model = None
        self.zone_model = None
        self._load()

    def _load(self) -> None:
        gait_path = self.artifact_dir / GAIT_MODEL_NAME
        zone_path = self.artifact_dir / ZONE_MODEL_NAME
        if gait_path.exists():
            self.gait_model = load_artifact(GAIT_MODEL_NAME) if self.artifact_dir == ARTIFACT_DIR else __import__("joblib").load(gait_path)
        if zone_path.exists():
            import joblib

            self.zone_model = joblib.load(zone_path)

    def analyze_window(
        self,
        frames: list[list[float]] | np.ndarray,
        sample_hz: float = 25.0,
        profile: ClinicalProfile | None = None,
        pressure_threshold: float = ALERT_PRESSURE_KPA,
        temperatures: list[list[float]] | None = None,
        ulcer_grade: int | None = None,
        ulcer_confidence: float = 0.0,
        compliance: float = 80.0,
    ) -> RiskResult:
        window = GaitWindow(
            np.asarray(frames, dtype=np.float64),
            sample_hz=sample_hz,
            temperature_c=None if temperatures is None else np.asarray(temperatures, dtype=np.float64),
        )
        feats = extract_features(window)
        x = feats.vector.reshape(1, -1)

        gait_pattern = "unknown"
        gait_p = 0.0
        zone = "none"
        zone_p = 0.0
        if self.gait_model is not None:
            gait_pattern, gait_p = _predict_label(self.gait_model, x)
        if self.zone_model is not None:
            zone, zone_p = _predict_label(self.zone_model, x)

        profile = profile or ClinicalProfile()
        clinical = clinical_risk_score(profile)
        peak = float(feats.extras.get("peak_any", 0.0))
        # pressure contribution: 0 at 40 kPa peak, 40 at 200 kPa
        pressure_score = float(np.clip((peak - 40.0) / (HIGH_RISK_PEAK_KPA - 40.0) * 40.0, 0, 40))
        temp_score = float(np.clip(feats.extras.get("temp_asym_max", 0.0) / 2.2 * 15.0, 0, 15))
        gait_score = 12.0 if gait_pattern not in ("normal", "unknown") else 0.0
        ulcer_score = 0.0
        if ulcer_grade is not None:
            ulcer_score = min(25.0, (ulcer_grade + 1) * 6.0 * max(ulcer_confidence, 0.35))
        compliance_penalty = max(0.0, (70.0 - compliance) * 0.25)
        health = float(
            np.clip(
                0.45 * clinical["clinical_score"]
                + pressure_score
                + temp_score
                + gait_score
                + ulcer_score
                + compliance_penalty,
                0,
                100,
            )
        )

        alerts: list[PressureAlert] = []
        last = window.pressure_kpa[-1]
        for foot, offset in (("left", 0), ("right", 4)):
            for site in SensorSite:
                value = float(last[offset + int(site)])
                if value >= pressure_threshold:
                    zone_name = SITE_TO_APP_ZONE[site]
                    alerts.append(
                        PressureAlert(
                            foot=foot,
                            site=site.name.lower(),
                            zone=zone_name,
                            value_kpa=value,
                            threshold_kpa=pressure_threshold,
                            message=f"High pressure on {foot} {SITE_TO_APP_ZONE[site]}: {value:.1f} kPa. Offload and check skin.",
                        )
                    )

        result = RiskResult(
            health_index=health,
            level=_level(health),
            gait_pattern=gait_pattern,
            gait_confidence=gait_p,
            high_risk_zone=zone,
            zone_confidence=zone_p,
            iwgdf_category=iwgdf_risk_category(profile),
            factors={
                "clinical": clinical["clinical_score"],
                "footPressure": pressure_score,
                "temperature": temp_score,
                "gait": gait_score,
                "ulcer": ulcer_score,
                "compliance": compliance,
            },
            alerts=alerts,
            extras=feats.extras,
            contributions=[],
        )
        result.contributions = contributions_as_dicts(result)
        return result


def latest_frame_to_app_zones(frame8: list[float]) -> dict:
    """Convert one 8-channel frame to the mobile FootData pressure fields."""

    def foot(offset: int) -> dict[str, float]:
        return {
            "toes": float(frame8[offset + SensorSite.MET1]),
            "ball": float(frame8[offset + SensorSite.MET2]),
            "arch": float(frame8[offset + SensorSite.MET5]),
            "heel": float(frame8[offset + SensorSite.HEEL]),
        }

    return {"left": foot(0), "right": foot(4)}
