"""Synthetic 4-FSR gait windows labeled from known biomechanical scenarios."""

from __future__ import annotations

import numpy as np

from xstep_ml.biomechanics import extract_features, GaitWindow
from xstep_ml.hardware import SensorSite
from xstep_ml.models.gait import GAIT_CLASSES, ZONE_CLASSES

GAIT_TO_ZONE = {
    "normal": "none",
    "left_forefoot_overload": "met2",
    "right_forefoot_overload": "met2",
    "left_heel_overload": "heel",
    "right_heel_overload": "heel",
    "left_lateral_overload": "met5",
    "right_lateral_overload": "met5",
    "asymmetric_antalgic": "met1",
    "shuffling_low_cadence": "none",
}


def _step_cycle(t: np.ndarray, cadence_spm: float, phase: float = 0.0) -> np.ndarray:
    freq = cadence_spm / 60.0
    return np.clip(np.sin(2 * np.pi * freq * t + phase), 0, None) ** 1.4


def synthesize_window(
    label: str,
    rng: np.random.Generator,
    seconds: float = 4.0,
    hz: float = 25.0,
) -> tuple[np.ndarray, str, str]:
    n = int(seconds * hz)
    t = np.arange(n) / hz
    cadence = {
        "shuffling_low_cadence": rng.uniform(68, 86),
        "asymmetric_antalgic": rng.uniform(88, 102),
    }.get(label, rng.uniform(100, 122))

    left_phase, right_phase = 0.0, np.pi
    l_cycle = _step_cycle(t, cadence, left_phase)
    r_cycle = _step_cycle(t, cadence, right_phase)

    # Typical walking: heel then forefoot. Scale in kPa.
    base = rng.uniform(28, 42)
    left = np.zeros((n, 4))
    right = np.zeros((n, 4))
    heel_wave = np.clip(np.sin(2 * np.pi * (cadence / 60.0) * t), 0, None)
    fore_wave = np.clip(np.sin(2 * np.pi * (cadence / 60.0) * t - 0.7), 0, None)

    left[:, SensorSite.HEEL] = base * 0.9 * heel_wave
    left[:, SensorSite.MET1] = base * 0.7 * fore_wave
    left[:, SensorSite.MET2] = base * 0.85 * fore_wave
    left[:, SensorSite.MET5] = base * 0.55 * fore_wave
    right[:, SensorSite.HEEL] = base * 0.9 * np.clip(np.sin(2 * np.pi * (cadence / 60.0) * t + np.pi), 0, None)
    right[:, SensorSite.MET1] = base * 0.7 * np.clip(np.sin(2 * np.pi * (cadence / 60.0) * t + np.pi - 0.7), 0, None)
    right[:, SensorSite.MET2] = base * 0.85 * np.clip(np.sin(2 * np.pi * (cadence / 60.0) * t + np.pi - 0.7), 0, None)
    right[:, SensorSite.MET5] = base * 0.55 * np.clip(np.sin(2 * np.pi * (cadence / 60.0) * t + np.pi - 0.7), 0, None)

    overload = rng.uniform(70, 140)
    if label == "left_forefoot_overload":
        left[:, SensorSite.MET1] += overload * fore_wave
        left[:, SensorSite.MET2] += overload * 1.1 * fore_wave
    elif label == "right_forefoot_overload":
        right[:, SensorSite.MET1] += overload * np.clip(np.sin(2 * np.pi * (cadence / 60.0) * t + np.pi - 0.7), 0, None)
        right[:, SensorSite.MET2] += overload * 1.1 * np.clip(np.sin(2 * np.pi * (cadence / 60.0) * t + np.pi - 0.7), 0, None)
    elif label == "left_heel_overload":
        left[:, SensorSite.HEEL] += overload * heel_wave
    elif label == "right_heel_overload":
        right[:, SensorSite.HEEL] += overload * np.clip(np.sin(2 * np.pi * (cadence / 60.0) * t + np.pi), 0, None)
    elif label == "left_lateral_overload":
        left[:, SensorSite.MET5] += overload * 1.2 * fore_wave
    elif label == "right_lateral_overload":
        right[:, SensorSite.MET5] += overload * 1.2 * np.clip(np.sin(2 * np.pi * (cadence / 60.0) * t + np.pi - 0.7), 0, None)
    elif label == "asymmetric_antalgic":
        left *= 0.45
        right[:, SensorSite.MET1] += overload * 0.6
    elif label == "shuffling_low_cadence":
        left *= 0.7
        right *= 0.7

    noise = rng.normal(0, 2.5, size=(n, 4))
    left = np.clip(left + noise, 0, None)
    right = np.clip(right + rng.normal(0, 2.5, size=(n, 4)), 0, None)
    frames = np.concatenate([left, right], axis=1)
    return frames, label, GAIT_TO_ZONE[label]


def make_dataset(n_per_class: int = 400, seed: int = 67) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    xs, ys_gait, ys_zone = [], [], []
    for gait in GAIT_CLASSES:
        for _ in range(n_per_class):
            frames, g, z = synthesize_window(gait, rng)
            feats = extract_features(GaitWindow(frames, sample_hz=25.0))
            xs.append(feats.vector)
            ys_gait.append(g)
            ys_zone.append(z)
    return np.vstack(xs), np.array(ys_gait), np.array(ys_zone)
