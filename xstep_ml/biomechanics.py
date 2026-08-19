"""Plantar biomechanics features from 4-FSR gait windows.

Features follow clinical DFU literature:
- peak plantar pressure (PPP)
- pressure-time integral (PTI)
- loading duration above a risk threshold
- left/right asymmetry
- cadence and stance ratio estimated from heel-strike peaks
- anterior-posterior center-of-pressure (forefoot vs heel)
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from xstep_ml.hardware import HIGH_RISK_PEAK_KPA, SensorSite

SITE_NAMES = ("met1", "met2", "met5", "heel")
_SITE_SUFFIXES = ("peak", "mean", "pti", "load", "high", "cv")
FEATURE_NAMES: list[str] = [
    f"{prefix}_{site}_{suf}"
    for prefix in ("L", "R")
    for site in SITE_NAMES
    for suf in _SITE_SUFFIXES
] + [
    "asym_met1",
    "asym_met2",
    "asym_met5",
    "asym_heel",
    "cadence_spm",
    "stance_ratio",
    "cop_ap",
    "forefoot_share",
    "peak_any",
    "pti_total",
    "temp_asym_max",
]


@dataclass
class GaitWindow:
    """Pressure time series. Shape (T, 8) = left[4] + right[4] in SensorSite order."""

    pressure_kpa: np.ndarray
    sample_hz: float = 25.0
    temperature_c: np.ndarray | None = None

    def __post_init__(self) -> None:
        arr = np.asarray(self.pressure_kpa, dtype=np.float64)
        if arr.ndim != 2 or arr.shape[1] != 8:
            raise ValueError(f"expected (T, 8) window, got {arr.shape}")
        self.pressure_kpa = arr


@dataclass
class BiomechanicalFeatures:
    vector: np.ndarray
    names: list[str] = field(default_factory=lambda: list(FEATURE_NAMES))
    extras: dict[str, float] = field(default_factory=dict)

    def as_dict(self) -> dict[str, float]:
        out = {n: float(v) for n, v in zip(self.names, self.vector)}
        out.update(self.extras)
        return out


def _peaks(signal: np.ndarray, min_distance: int) -> np.ndarray:
    if len(signal) < 3:
        return np.array([], dtype=int)
    greater = (signal[1:-1] > signal[:-2]) & (signal[1:-1] >= signal[2:])
    idx = np.where(greater)[0] + 1
    if len(idx) == 0:
        return idx
    keep = [idx[0]]
    for i in idx[1:]:
        if i - keep[-1] >= min_distance:
            keep.append(i)
    return np.array(keep, dtype=int)


def extract_features(window: GaitWindow, risk_kpa: float = HIGH_RISK_PEAK_KPA) -> BiomechanicalFeatures:
    p = window.pressure_kpa
    hz = float(window.sample_hz)
    dt = 1.0 / max(hz, 1e-6)
    left, right = p[:, :4], p[:, 4:]
    extras: dict[str, float] = {}
    feats: list[float] = []

    def site_block(arr: np.ndarray, prefix: str) -> None:
        peaks = arr.max(axis=0)
        means = arr.mean(axis=0)
        pti = arr.sum(axis=0) * dt
        load_frac = (arr > 30.0).mean(axis=0)
        high_frac = (arr > risk_kpa).mean(axis=0)
        cv = arr.std(axis=0) / np.maximum(means, 1e-3)
        for i, name in enumerate(SITE_NAMES):
            feats.extend(
                [
                    float(peaks[i]),
                    float(means[i]),
                    float(pti[i]),
                    float(load_frac[i]),
                    float(high_frac[i]),
                    float(cv[i]),
                ]
            )
            extras[f"{prefix}_{name}_peak"] = float(peaks[i])
            extras[f"{prefix}_{name}_pti"] = float(pti[i])

    site_block(left, "L")
    site_block(right, "R")

    l_peak, r_peak = left.max(axis=0), right.max(axis=0)
    denom = np.maximum((l_peak + r_peak) / 2.0, 1e-3)
    asym = np.abs(l_peak - r_peak) / denom
    feats.extend(float(x) for x in asym)

    # Use mean of both heels for strike detection
    heel_mean = (left[:, SensorSite.HEEL] + right[:, SensorSite.HEEL]) / 2.0
    min_dist = max(int(0.35 * hz), 3)
    strikes = _peaks(heel_mean, min_dist)
    duration_s = len(p) * dt
    cadence = (len(strikes) / max(duration_s, 1e-6)) * 60.0
    loaded = (p.max(axis=1) > 15.0).mean()
    fore = p[:, [SensorSite.MET1, SensorSite.MET2, SensorSite.MET5, 4 + SensorSite.MET1, 4 + SensorSite.MET2, 4 + SensorSite.MET5]]
    total = max(float(p.sum()), 1e-6)
    cop_ap = float(fore.sum() / total)
    feats.extend(
        [
            float(cadence),
            float(loaded),
            cop_ap,
            cop_ap,
            float(p.max()),
            float(p.sum() * dt),
        ]
    )

    temp_asym = 0.0
    if window.temperature_c is not None:
        t = np.asarray(window.temperature_c, dtype=np.float64)
        if t.shape == p.shape:
            temp_asym = float(np.max(np.abs(t[:, :4].mean(axis=0) - t[:, 4:].mean(axis=0))))
    feats.append(temp_asym)
    extras["cadence_spm"] = float(cadence)
    extras["peak_any"] = float(p.max())
    extras["temp_asym_max"] = temp_asym
    extras["stance_ratio"] = float(loaded)
    extras["cop_ap"] = cop_ap
    extras["pti_total"] = float(p.sum() * dt)
    extras["asym_met1"] = float(asym[0])
    extras["asym_met2"] = float(asym[1])
    extras["asym_met5"] = float(asym[2])
    extras["asym_heel"] = float(asym[3])
    try:
        from xstep_ml.features import extended_from_window

        extras.update(extended_from_window(window, risk_kpa=risk_kpa))
    except ImportError:
        pass

    vector = np.array(feats, dtype=np.float64)
    names = list(FEATURE_NAMES)
    if len(vector) != len(names):
        names = [f"f{i}" for i in range(len(vector))]
    return BiomechanicalFeatures(vector=vector, names=names, extras=extras)


def window_from_frames(frames: list[list[float]], sample_hz: float = 25.0) -> GaitWindow:
    return GaitWindow(pressure_kpa=np.asarray(frames, dtype=np.float64), sample_hz=sample_hz)
