"""Simulated wearable perturbations for robustness curves.

All perturbations are engineering stress tests on synthetic or recorded
pressure windows. They are not clinical noise models unless so labeled.
"""

from __future__ import annotations

import numpy as np

from xstep_ml.data.schema import CANONICAL_SITES


def gaussian_noise(windows: np.ndarray, rng: np.random.Generator, sigma_kpa: float) -> np.ndarray:
    out = windows + rng.normal(0.0, sigma_kpa, size=windows.shape)
    return np.clip(out, 0.0, None)


def calibration_drift(windows: np.ndarray, rng: np.random.Generator, max_gain_frac: float) -> np.ndarray:
    n, t, c = windows.shape
    gains = 1.0 + rng.uniform(-max_gain_frac, max_gain_frac, size=(n, 1, c))
    t_idx = np.linspace(0.0, 1.0, t).reshape(1, t, 1)
    return np.clip(windows * (1.0 + (gains - 1.0) * t_idx), 0.0, None)


def dropped_packets(windows: np.ndarray, rng: np.random.Generator, drop_frac: float) -> np.ndarray:
    out = windows.copy()
    mask = rng.random(out.shape[:2]) < drop_frac
    out[mask] = 0.0
    return out


def missing_sensor(windows: np.ndarray, site_index: int) -> np.ndarray:
    out = windows.copy()
    out[:, :, site_index] = 0.0
    out[:, :, site_index + 4] = 0.0
    return out


def short_dropout(windows: np.ndarray, rng: np.random.Generator, length: int) -> np.ndarray:
    out = windows.copy()
    n, t, _c = out.shape
    length = max(1, min(length, t))
    for i in range(n):
        start = int(rng.integers(0, max(t - length + 1, 1)))
        out[i, start : start + length, :] = 0.0
    return out


def sensor_bias(windows: np.ndarray, bias_kpa: float) -> np.ndarray:
    return np.clip(windows + bias_kpa, 0.0, None)


def downsample(windows: np.ndarray, factor: int) -> np.ndarray:
    factor = max(int(factor), 1)
    return windows[:, ::factor, :].copy()


def resample_to_length(windows: np.ndarray, target_t: int) -> np.ndarray:
    n, t, c = windows.shape
    if t == target_t:
        return windows.copy()
    src = np.linspace(0.0, 1.0, t)
    dst = np.linspace(0.0, 1.0, target_t)
    out = np.empty((n, target_t, c), dtype=windows.dtype)
    for i in range(n):
        for j in range(c):
            out[i, :, j] = np.interp(dst, src, windows[i, :, j])
    return out


def timing_jitter(windows: np.ndarray, rng: np.random.Generator, jitter_frac: float) -> np.ndarray:
    """Irregular sampling then linear resample back to the original grid."""
    n, t, c = windows.shape
    out = np.empty_like(windows)
    grid = np.linspace(0.0, 1.0, t)
    for i in range(n):
        noise = rng.uniform(-jitter_frac, jitter_frac, size=t)
        noise[0] = 0.0
        noise[-1] = 0.0
        tau = np.sort(np.clip(grid + noise / max(t - 1, 1), 0.0, 1.0))
        tau[0], tau[-1] = 0.0, 1.0
        for j in range(c):
            out[i, :, j] = np.interp(grid, tau, windows[i, :, j])
    return np.clip(out, 0.0, None)


def mask_sites(windows: np.ndarray, keep_sites: list[int]) -> np.ndarray:
    out = np.zeros_like(windows)
    for s in keep_sites:
        out[:, :, s] = windows[:, :, s]
        out[:, :, s + 4] = windows[:, :, s + 4]
    return out


SENSOR_SUBSETS: dict[str, list[int]] = {
    "4_all": [0, 1, 2, 3],
    "3_no_met1": [1, 2, 3],
    "3_no_met2": [0, 2, 3],
    "3_no_met5": [0, 1, 3],
    "3_no_heel": [0, 1, 2],
    "2_met2_heel": [1, 3],
    "2_met1_heel": [0, 3],
    "2_met1_met2": [0, 1],
    "1_met2": [1],
    "1_heel": [3],
    "1_met1": [0],
    "1_met5": [2],
}


def subset_label(key: str) -> str:
    sites = SENSOR_SUBSETS[key]
    names = [CANONICAL_SITES[i] for i in sites]
    return f"{len(sites)}-site ({'+'.join(names)})"
