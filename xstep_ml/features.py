"""Documented biomechanical feature specifications and extended extractors.

Production models use the 59-D vector from `xstep_ml.biomechanics.extract_features`.
This module adds mathematically defined extras without changing that vector length.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from xstep_ml.biomechanics import GaitWindow, extract_features
from xstep_ml.hardware import HIGH_RISK_PEAK_KPA, SensorSite

SITE_NAMES = ("met1", "met2", "met5", "heel")
CONTACT_KPA = 15.0
LOADED_KPA = 30.0


@dataclass(frozen=True)
class FeatureSpec:
    name: str
    definition: str
    unit: str
    interpretation: str
    group: str


FEATURE_SPEC: dict[str, FeatureSpec] = {}


def _spec(name: str, definition: str, unit: str, interpretation: str, group: str) -> None:
    FEATURE_SPEC[name] = FeatureSpec(name, definition, unit, interpretation, group)


def _init_specs() -> None:
    if FEATURE_SPEC:
        return
    for prefix, foot in (("L", "left"), ("R", "right")):
        for site in SITE_NAMES:
            _spec(
                f"{prefix}_{site}_peak",
                r"PPP = max_t p_{site}(t)",
                "kPa",
                f"Peak plantar pressure at the {foot} {site} during the window.",
                "pressure",
            )
            _spec(
                f"{prefix}_{site}_mean",
                r"mean_t p_{site}(t)",
                "kPa",
                f"Mean pressure at the {foot} {site}.",
                "pressure",
            )
            _spec(
                f"{prefix}_{site}_pti",
                r"PTI = sum_t p_{site}(t) Δt",
                "kPa·s",
                f"Pressure-time integral (cumulative load) at the {foot} {site}.",
                "pti",
            )
            _spec(
                f"{prefix}_{site}_load",
                r"mean_t 1[p_{site}(t) > 30 kPa]",
                "1",
                "Fraction of samples above the loaded-contact engineering threshold (30 kPa).",
                "temporal",
            )
            _spec(
                f"{prefix}_{site}_high",
                r"mean_t 1[p_{site}(t) > τ_high]",
                "1",
                "Fraction of samples above the literature high-risk PPP band (default 200 kPa).",
                "temporal",
            )
            _spec(
                f"{prefix}_{site}_cv",
                r"std(p) / max(mean(p), ε)",
                "1",
                "Coefficient of variation (temporal variability) at the site.",
                "temporal",
            )
    for site in SITE_NAMES:
        _spec(
            f"asym_{site}",
            r"|PPP_L - PPP_R| / ((PPP_L + PPP_R)/2)",
            "1",
            f"Bilateral peak-pressure symmetry index at {site}.",
            "symmetry",
        )
    _spec("cadence_spm", "60 × (heel-strike count) / window duration", "steps/min", "Estimated walking cadence.", "temporal")
    _spec("stance_ratio", "mean_t 1[max_site p(t) > 15 kPa]", "1", "Approximate duty factor (loaded fraction).", "temporal")
    _spec("cop_ap", "sum(forefoot channels) / sum(all channels)", "1", "Anterior–posterior pressure-mass share (forefoot).", "pressure")
    _spec("forefoot_share", "same as cop_ap", "1", "Alias of anterior pressure share.", "pressure")
    _spec("peak_any", "max_{sites,t} p", "kPa", "Window-wise peak plantar pressure across both feet.", "pressure")
    _spec("pti_total", "sum_{sites,t} p Δt", "kPa·s", "Total pressure-time integral over the window.", "pti")
    _spec("temp_asym_max", "max_site |mean T_L - mean T_R|", "°C", "Optional thermal asymmetry; 0 if no thermistors.", "thermal")
    # Extended (not in the 59-D production vector)
    _spec("loading_rate_max", "max_t (dp/dt)_rising on peak channel", "kPa/s", "Peak loading rate.", "temporal")
    _spec("unloading_rate_min", "min_t (dp/dt)_falling on peak channel", "kPa/s", "Peak unloading rate (negative).", "temporal")
    _spec("contact_duration_s", "sum_t 1[max p > 15 kPa] Δt", "s", "Loaded contact duration in the window.", "temporal")
    _spec("stride_duration_s", "median inter-heel-strike interval", "s", "Stride time if ≥2 heel strikes; else NaN-safe 0.", "temporal")
    _spec("stance_duration_s", "contact_duration / max(n_strikes, 1)", "s", "Crude stance duration estimate.", "temporal")
    _spec("swing_duration_s", "max(stride_duration - stance_duration, 0)", "s", "Crude swing duration if stride is defined.", "temporal")
    _spec("cop_ml", "(Σ MET5 − Σ MET1) / (Σ MET5 + Σ MET1)", "1", "Medial–lateral centroid approximation.", "pressure")
    _spec("forefoot_heel_ratio", "Σ forefoot / max(Σ heel, ε)", "1", "Regional pressure ratio (forefoot vs heel).", "pressure")
    _spec("overload_duration_s", "sum_t 1[max p > τ_alert] Δt", "s", "Duration above the engineering alert threshold.", "pti")
    _spec("overload_events", "count of contiguous runs with max p > τ_alert", "1", "Repeated overload event count.", "pti")
    _spec("cumulative_overload_pti", "sum_t max(p_max(t) − τ_alert, 0) Δt", "kPa·s", "Cumulative exposure above the alert threshold.", "pti")
    _spec("l_r_load_asym", "|sum L − sum R| / ((sum L + sum R)/2)", "1", "Whole-foot load symmetry.", "symmetry")


_init_specs()

EXTENDED_NAMES = (
    "loading_rate_max",
    "unloading_rate_min",
    "contact_duration_s",
    "stride_duration_s",
    "stance_duration_s",
    "swing_duration_s",
    "cop_ml",
    "forefoot_heel_ratio",
    "overload_duration_s",
    "overload_events",
    "cumulative_overload_pti",
    "l_r_load_asym",
)


def _count_runs(mask: np.ndarray) -> int:
    if mask.size == 0:
        return 0
    padded = np.concatenate([[False], mask.astype(bool), [False]])
    return int(np.sum((~padded[:-1]) & padded[1:]))


def _heel_strikes(heel_mean: np.ndarray, hz: float) -> np.ndarray:
    min_distance = max(int(0.35 * hz), 3)
    if len(heel_mean) < 3:
        return np.array([], dtype=int)
    greater = (heel_mean[1:-1] > heel_mean[:-2]) & (heel_mean[1:-1] >= heel_mean[2:])
    idx = np.where(greater)[0] + 1
    keep: list[int] = []
    for i in idx:
        if not keep or i - keep[-1] >= min_distance:
            keep.append(int(i))
    return np.asarray(keep, dtype=int)


def extended_from_window(
    window: GaitWindow,
    *,
    risk_kpa: float = HIGH_RISK_PEAK_KPA,
    alert_kpa: float = 75.0,
) -> dict[str, float]:
    p = window.pressure_kpa
    hz = float(window.sample_hz)
    dt = 1.0 / max(hz, 1e-6)
    left, right = p[:, :4], p[:, 4:]
    pmax = p.max(axis=1)
    dp = np.diff(pmax, prepend=pmax[:1]) / dt
    loading = float(np.max(dp))
    unloading = float(np.min(dp))
    contact_mask = pmax > CONTACT_KPA
    contact_s = float(contact_mask.sum() * dt)
    heel_mean = (left[:, SensorSite.HEEL] + right[:, SensorSite.HEEL]) / 2.0
    strikes = _heel_strikes(heel_mean, hz)
    if len(strikes) >= 2:
        stride = float(np.median(np.diff(strikes)) * dt)
    else:
        stride = 0.0
    n_strikes = max(len(strikes), 1)
    stance = contact_s / n_strikes
    swing = max(stride - stance, 0.0) if stride > 0 else 0.0
    met1 = p[:, [SensorSite.MET1, 4 + SensorSite.MET1]].sum()
    met5 = p[:, [SensorSite.MET5, 4 + SensorSite.MET5]].sum()
    heel = p[:, [SensorSite.HEEL, 4 + SensorSite.HEEL]].sum()
    fore = p[:, [SensorSite.MET1, SensorSite.MET2, SensorSite.MET5, 4 + SensorSite.MET1, 4 + SensorSite.MET2, 4 + SensorSite.MET5]].sum()
    cop_ml = float((met5 - met1) / max(met5 + met1, 1e-6))
    fh = float(fore / max(heel, 1e-6))
    over_mask = pmax > alert_kpa
    over_s = float(over_mask.sum() * dt)
    events = _count_runs(over_mask)
    cum = float(np.maximum(pmax - alert_kpa, 0.0).sum() * dt)
    lsum, rsum = float(left.sum()), float(right.sum())
    lr_asym = abs(lsum - rsum) / max((lsum + rsum) / 2.0, 1e-6)
    return {
        "loading_rate_max": loading,
        "unloading_rate_min": unloading,
        "contact_duration_s": contact_s,
        "stride_duration_s": stride,
        "stance_duration_s": stance,
        "swing_duration_s": swing,
        "cop_ml": cop_ml,
        "forefoot_heel_ratio": fh,
        "overload_duration_s": over_s,
        "overload_events": float(events),
        "cumulative_overload_pti": cum,
        "l_r_load_asym": float(lr_asym),
    }


def extract_extended_features(window: GaitWindow, risk_kpa: float = HIGH_RISK_PEAK_KPA) -> tuple[np.ndarray, list[str]]:
    core = extract_features(window, risk_kpa=risk_kpa)
    extra = extended_from_window(window, risk_kpa=risk_kpa)
    vec = np.concatenate([core.vector, np.array([extra[n] for n in EXTENDED_NAMES], dtype=np.float64)])
    names = list(core.names) + list(EXTENDED_NAMES)
    return vec, names


def feature_groups(names: list[str]) -> dict[str, list[int]]:
    """Index sets for feature-ablation experiments."""
    def idx(pred) -> list[int]:
        return [i for i, n in enumerate(names) if pred(n)]

    return {
        "raw_pressure": idx(lambda n: n.endswith("_peak") or n.endswith("_mean") or n in ("peak_any", "cop_ap", "forefoot_share", "cop_ml", "forefoot_heel_ratio")),
        "temporal": idx(lambda n: n.endswith("_load") or n.endswith("_cv") or n.endswith("_high") or n in ("cadence_spm", "stance_ratio", "loading_rate_max", "unloading_rate_min", "contact_duration_s", "stride_duration_s", "stance_duration_s", "swing_duration_s")),
        "pti": idx(lambda n: "pti" in n or n in ("overload_duration_s", "overload_events", "cumulative_overload_pti") or n.endswith("_high")),
        "symmetry": idx(lambda n: n.startswith("asym_") or n == "l_r_load_asym"),
        "combined": list(range(len(names))),
    }
