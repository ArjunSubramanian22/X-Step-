"""Decomposable engineering risk contributions (not LLM, not diagnosis)."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from xstep_ml.hardware import ALERT_PRESSURE_KPA, HIGH_RISK_PEAK_KPA


@dataclass
class RiskContribution:
    name: str
    value: float
    unit: str
    direction: str
    weight: float
    contribution: float
    note: str


def decompose_risk(result, extras: dict[str, float] | None = None) -> list[RiskContribution]:
    """Attribute the engineering index to inspectable pressure/gait factors."""
    ex = extras or result.extras
    peak = float(ex.get("peak_any", 0.0))
    cadence = float(ex.get("cadence_spm", 0.0))
    temp = float(ex.get("temp_asym_max", 0.0))
    l_fore = float(ex.get("L_met1_peak", 0.0)) + float(ex.get("L_met2_peak", 0.0))
    r_fore = float(ex.get("R_met1_peak", 0.0)) + float(ex.get("R_met2_peak", 0.0))
    fore = max(l_fore, r_fore)
    asym_vals = [float(ex.get(k, 0.0)) for k in ("asym_met1", "asym_met2", "asym_met5", "asym_heel")]
    # extras from extended features may be absent
    contact = float(ex.get("contact_duration_s", ex.get("stance_ratio", 0.0)))
    events = float(ex.get("overload_events", 0.0))
    trend = float(ex.get("longitudinal_pti_slope", 0.0))

    items = [
        RiskContribution(
            "elevated_forefoot_load",
            fore,
            "kPa",
            "raises_risk",
            0.25,
            float(np.clip((fore - 80.0) / 200.0 * 25.0, 0, 25)),
            "Peak of MET1+MET2 on the more loaded foot.",
        ),
        RiskContribution(
            "repeated_peak_pressure",
            events if events else peak,
            "events" if events else "kPa",
            "raises_risk",
            0.2,
            float(np.clip((peak - 40.0) / (HIGH_RISK_PEAK_KPA - 40.0) * 20.0, 0, 20)),
            f"Window peak vs engineering high-load band; alert threshold {ALERT_PRESSURE_KPA} kPa is not clinically validated.",
        ),
        RiskContribution(
            "asymmetry",
            float(np.mean(asym_vals)) if asym_vals else 0.0,
            "1",
            "raises_risk",
            0.15,
            float(np.clip(np.mean(asym_vals) * 15.0, 0, 15)),
            "Mean bilateral PPP symmetry index across four sites.",
        ),
        RiskContribution(
            "prolonged_contact",
            contact,
            "s or fraction",
            "raises_risk",
            0.1,
            float(np.clip(contact / 4.0 * 10.0, 0, 10)) if contact > 1 else float(np.clip(contact * 10.0, 0, 10)),
            "Longer loaded contact increases cumulative exposure in a window.",
        ),
        RiskContribution(
            "gait_pattern",
            1.0 if result.gait_pattern not in ("normal", "unknown") else 0.0,
            "class",
            "raises_risk",
            0.12,
            float(result.factors.get("gait", 0.0)),
            f"Pattern={result.gait_pattern} (engineering class, not a diagnosis).",
        ),
        RiskContribution(
            "clinical_prior",
            float(result.factors.get("clinical", 0.0)),
            "score",
            "raises_risk",
            0.45,
            float(0.45 * result.factors.get("clinical", 0.0)),
            "IWGDF-style questionnaire prior; not learned from pressure.",
        ),
        RiskContribution(
            "thermal_asymmetry",
            temp,
            "°C",
            "raises_risk",
            0.1,
            float(result.factors.get("temperature", 0.0)),
            "Reserved thermistor field; literature 2.2 °C heuristic if measured.",
        ),
        RiskContribution(
            "longitudinal_trend",
            trend,
            "kPa·s / session",
            "raises_risk",
            0.08,
            float(np.clip(trend, 0, 8)),
            "Requires repeated sessions; 0 if no history is available.",
        ),
        RiskContribution(
            "low_cadence",
            cadence,
            "steps/min",
            "raises_risk" if cadence and cadence < 90 else "neutral",
            0.05,
            4.0 if cadence and cadence < 90 else 0.0,
            "Shuffling/low cadence is an engineering gait flag.",
        ),
    ]
    return items


def contributions_as_dicts(result) -> list[dict]:
    return [asdict(c) for c in decompose_risk(result)]
