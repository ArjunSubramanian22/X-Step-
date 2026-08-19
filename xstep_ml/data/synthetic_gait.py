"""In-silico 4-FSR gait cohort with inter-subject variability.

IID random splits of easy sinusoids inflate accuracy. This generator models
virtual subjects (mass, FSR gain mismatch, offset drift) and mixed-severity
overload so evaluation can use group/subject-wise cross-validation.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from xstep_ml.biomechanics import FEATURE_NAMES, GaitWindow, extract_features
from xstep_ml.hardware import SensorSite
from xstep_ml.models.gait import GAIT_CLASSES

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


@dataclass
class SubjectParams:
    subject_id: int
    mass_scale: float
    fsr_gain: np.ndarray  # (8,)
    offset_kpa: np.ndarray  # (8,)
    cadence_bias: float
    drop_prob: float


def _wave(t: np.ndarray, cadence_spm: float, phase: float) -> np.ndarray:
    s = np.sin(2 * np.pi * (cadence_spm / 60.0) * t + phase)
    return np.clip(s, 0, None) ** 1.35


def sample_subject(rng: np.random.Generator, subject_id: int) -> SubjectParams:
    return SubjectParams(
        subject_id=subject_id,
        mass_scale=float(rng.uniform(0.78, 1.32)),
        fsr_gain=rng.uniform(0.82, 1.18, size=8),
        offset_kpa=rng.normal(0.0, 4.0, size=8),
        cadence_bias=float(rng.normal(0.0, 6.0)),
        drop_prob=float(rng.uniform(0.0, 0.04)),
    )


def synthesize_window(
    label: str,
    rng: np.random.Generator,
    seconds: float = 4.0,
    hz: float = 25.0,
    subject: SubjectParams | None = None,
    severity: float | None = None,
    noise_std: float = 3.5,
) -> tuple[np.ndarray, str, str]:
    n = int(seconds * hz)
    t = np.arange(n) / hz
    base_cadence = {
        "shuffling_low_cadence": rng.uniform(70, 88),
        "asymmetric_antalgic": rng.uniform(86, 104),
    }.get(label, rng.uniform(98, 124))
    if subject:
        base_cadence = float(np.clip(base_cadence + subject.cadence_bias, 62, 130))

    mass = subject.mass_scale if subject else 1.0
    base = rng.uniform(26, 44) * mass
    severity = rng.uniform(0.25, 1.0) if severity is None else float(severity)
    overload = rng.uniform(35, 120) * severity * mass

    l_heel = _wave(t, base_cadence, 0.0)
    l_fore = _wave(t, base_cadence, -0.72)
    r_heel = _wave(t, base_cadence, np.pi)
    r_fore = _wave(t, base_cadence, np.pi - 0.72)

    left = np.zeros((n, 4))
    right = np.zeros((n, 4))
    left[:, SensorSite.HEEL] = base * 0.95 * l_heel
    left[:, SensorSite.MET1] = base * 0.72 * l_fore
    left[:, SensorSite.MET2] = base * 0.88 * l_fore
    left[:, SensorSite.MET5] = base * 0.58 * l_fore
    right[:, SensorSite.HEEL] = base * 0.95 * r_heel
    right[:, SensorSite.MET1] = base * 0.72 * r_fore
    right[:, SensorSite.MET2] = base * 0.88 * r_fore
    right[:, SensorSite.MET5] = base * 0.58 * r_fore

    if label == "left_forefoot_overload":
        left[:, SensorSite.MET1] += overload * 0.85 * l_fore
        left[:, SensorSite.MET2] += overload * l_fore
    elif label == "right_forefoot_overload":
        right[:, SensorSite.MET1] += overload * 0.85 * r_fore
        right[:, SensorSite.MET2] += overload * r_fore
    elif label == "left_heel_overload":
        left[:, SensorSite.HEEL] += overload * l_heel
    elif label == "right_heel_overload":
        right[:, SensorSite.HEEL] += overload * r_heel
    elif label == "left_lateral_overload":
        left[:, SensorSite.MET5] += overload * 1.15 * l_fore
    elif label == "right_lateral_overload":
        right[:, SensorSite.MET5] += overload * 1.15 * r_fore
    elif label == "asymmetric_antalgic":
        left *= 0.55 + 0.25 * (1 - severity)
        right[:, SensorSite.MET1] += overload * 0.45 * r_fore
    elif label == "shuffling_low_cadence":
        left *= 0.65
        right *= 0.65

    frames = np.concatenate([left, right], axis=1)
    if subject is not None:
        frames = frames * subject.fsr_gain.reshape(1, 8) + subject.offset_kpa.reshape(1, 8)
        if subject.drop_prob > 0:
            mask = rng.random(frames.shape) < subject.drop_prob
            frames[mask] = 0.0
    frames = np.clip(frames + rng.normal(0.0, noise_std, size=frames.shape), 0, None)
    return frames, label, GAIT_TO_ZONE[label]


@dataclass
class CohortBundle:
    """Grouped synthetic (or later real) pressure-window cohort.

    `data_source` must remain `synthetic` until human traces are substituted
    without changing the experiment runner.
    """

    X: np.ndarray
    y_gait: np.ndarray
    y_zone: np.ndarray
    subject_id: np.ndarray
    session_id: np.ndarray
    windows: np.ndarray
    sample_hz: float
    window_seconds: float
    feature_names: list[str]
    data_source: str = "synthetic"
    calibration_version: str = "linear_adc_engineering_v0"
    firmware_version: str = "sim-0"


def make_dataset(n_per_class: int = 400, seed: int = 67) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Backward-compatible IID set (no subject ids)."""
    x, y_gait, y_zone, _ = make_cohort(n_subjects=1, windows_per_class=n_per_class, seed=seed)
    return x, y_gait, y_zone


def make_cohort_bundle(
    n_subjects: int = 24,
    windows_per_class: int = 12,
    seed: int = 67,
    hz: float = 25.0,
    seconds: float = 4.0,
    noise_std: float = 3.5,
    label_noise: float = 0.03,
) -> CohortBundle:
    """Generate windows + features + subject/session ids (engineering simulation)."""
    rng = np.random.default_rng(seed)
    xs, ys_gait, ys_zone, sids, sess, wins = [], [], [], [], [], []
    for sid in range(n_subjects):
        subj = sample_subject(rng, sid)
        for gait_i, gait in enumerate(GAIT_CLASSES):
            session = f"s{sid}_g{gait_i}"
            for _ in range(windows_per_class):
                frames, g, z = synthesize_window(
                    gait, rng, seconds=seconds, hz=hz, subject=subj, noise_std=noise_std
                )
                if rng.random() < label_noise:
                    g = str(rng.choice(GAIT_CLASSES))
                    z = GAIT_TO_ZONE[g]
                feats = extract_features(GaitWindow(frames, sample_hz=hz))
                xs.append(feats.vector)
                ys_gait.append(g)
                ys_zone.append(z)
                sids.append(sid)
                sess.append(session)
                wins.append(frames)
    names = list(feats.names) if xs else list(FEATURE_NAMES)
    return CohortBundle(
        X=np.vstack(xs),
        y_gait=np.array(ys_gait),
        y_zone=np.array(ys_zone),
        subject_id=np.array(sids, dtype=np.int32),
        session_id=np.array(sess, dtype=object),
        windows=np.stack(wins, axis=0),
        sample_hz=float(hz),
        window_seconds=float(seconds),
        feature_names=names,
        data_source="synthetic",
    )


def make_cohort(
    n_subjects: int = 24,
    windows_per_class: int = 12,
    seed: int = 67,
    hz: float = 25.0,
    noise_std: float = 3.5,
    label_noise: float = 0.03,
    seconds: float = 4.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return X, y_gait, y_zone, subject_id."""
    bundle = make_cohort_bundle(
        n_subjects=n_subjects,
        windows_per_class=windows_per_class,
        seed=seed,
        hz=hz,
        seconds=seconds,
        noise_std=noise_std,
        label_noise=label_noise,
    )
    return bundle.X, bundle.y_gait, bundle.y_zone, bundle.subject_id
