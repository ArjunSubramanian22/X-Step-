"""IWGDF-inspired clinical DFU risk from onboarding / medical record."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ClinicalProfile:
    diabetes_duration_years: float = 0.0
    hba1c: float = 7.0
    neuropathy: str = "None"  # None | Mild | Moderate | Severe
    prior_ulcer: bool = False
    amputation: bool = False
    vascular: bool = False
    smoking: str = "Never"
    age: float = 50.0
    work_type: str = "Sedentary"


def iwgdf_risk_category(profile: ClinicalProfile) -> int:
    """
    Approximate IWGDF risk:
      0 very low, 1 low (neuropathy), 2 moderate (neuropathy + PAD or deformity),
      3 high (ulcer or amputation history).
    """
    if profile.amputation or profile.prior_ulcer:
        return 3
    neuro = profile.neuropathy not in ("None", "", "none")
    if neuro and profile.vascular:
        return 2
    if neuro:
        return 1
    return 0


def clinical_risk_score(profile: ClinicalProfile) -> dict[str, float]:
    """Return 0-100 clinical contribution plus factor breakdown."""
    category = iwgdf_risk_category(profile)
    neuro_map = {"None": 0, "Mild": 12, "Moderate": 22, "Severe": 32}
    neuro = neuro_map.get(profile.neuropathy, 0)
    glycemic = 0.0
    if profile.hba1c > 8.5:
        glycemic = 22.0
    elif profile.hba1c > 7.5:
        glycemic = 14.0
    elif profile.hba1c > 6.5:
        glycemic = 7.0
    duration = min(profile.diabetes_duration_years, 30.0) * 0.4
    history = 28.0 if profile.amputation else 18.0 if profile.prior_ulcer else 0.0
    vascular = 12.0 if profile.vascular else 0.0
    smoking = 10.0 if profile.smoking == "Current" else 4.0 if profile.smoking == "Former" else 0.0
    standing = 6.0 if profile.work_type in ("Standing", "Walking", "Physical Labor") else 0.0
    raw = neuro + glycemic + duration + history + vascular + smoking + standing
    score = float(min(100.0, raw))
    return {
        "clinical_score": score,
        "iwgdf_category": float(category),
        "neuropathy": float(neuro),
        "glycemic": float(glycemic),
        "ulcer_history": float(history),
        "vascular": float(vascular),
        "smoking": float(smoking),
    }
