"""FSR ADC → resistance → force/pressure calibration.

The production firmware currently uses a linear ADC→kPa map
(`xstep_ml.hardware.adc_to_kpa`) as an engineering default. This module is the
research calibration pipeline: voltage-divider inversion, configurable
(including nonlinear) curves, residual/repeatability/hysteresis/drift helpers,
and publication plots.

If no bench dataset is present, only the **schema** and **simulated examples**
are used. Simulated curves are labeled as such and are not device measurements.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from xstep_ml.hardware import ADC_FULL_SCALE, SensorSite


@dataclass
class SensorCalibration:
    """Per-sensor calibration parameters.

    Force model (Interlink-style log–log, used only when `model="loglog"`):

        log10(F_N) = a + b * log10(R_ohm)

    Linear fallback (`model="linear_adc"`) matches the current firmware map:

        P_kPa = (adc / ADC_FULL_SCALE) * kpa_full_scale
    """

    site: str
    r_fixed_ohm: float = 10_000.0
    vcc_v: float = 3.3
    adc_full_scale: float = ADC_FULL_SCALE
    model: str = "linear_adc"
    loglog_a: float = 3.0
    loglog_b: float = -0.7
    area_m2: float = 1.267e-4  # ~12.7 mm diameter active area (FSR402-class)
    kpa_full_scale: float = 250.0
    version: str = "unmeasured_engineering_v0"


DEFAULT_CALIBRATIONS: dict[str, SensorCalibration] = {
    site.name.lower(): SensorCalibration(site=site.name.lower()) for site in SensorSite
}


def adc_to_resistance_ohm(adc: np.ndarray | float, cal: SensorCalibration) -> np.ndarray:
    """Invert a high-side FSR / low-side Rf voltage divider.

    Vout = Vcc * Rf / (R_fsr + Rf)  →  R_fsr = Rf * (ADC_FS / ADC - 1)
    """
    x = np.asarray(adc, dtype=np.float64)
    x = np.clip(x, 1.0, cal.adc_full_scale - 1.0)
    return cal.r_fixed_ohm * (cal.adc_full_scale / x - 1.0)


def resistance_to_force_n(resistance_ohm: np.ndarray | float, cal: SensorCalibration) -> np.ndarray:
    r = np.clip(np.asarray(resistance_ohm, dtype=np.float64), 1.0, 1e8)
    log_f = cal.loglog_a + cal.loglog_b * np.log10(r)
    return np.clip(10.0 ** log_f, 0.0, 500.0)


def force_n_to_pressure_kpa(force_n: np.ndarray | float, cal: SensorCalibration) -> np.ndarray:
    area = max(cal.area_m2, 1e-8)
    pa = np.asarray(force_n, dtype=np.float64) / area
    return pa / 1000.0


def adc_to_pressure_kpa(adc: np.ndarray | float, cal: SensorCalibration) -> np.ndarray:
    if cal.model == "linear_adc":
        x = np.asarray(adc, dtype=np.float64)
        return np.clip(x / cal.adc_full_scale * cal.kpa_full_scale, 0.0, None)
    r = adc_to_resistance_ohm(adc, cal)
    f = resistance_to_force_n(r, cal)
    return force_n_to_pressure_kpa(f, cal)


def fit_loglog(resistance_ohm: np.ndarray, force_n: np.ndarray) -> tuple[float, float]:
    """Ordinary least squares in log10–log10 space. Requires physical measurements."""
    r = np.asarray(resistance_ohm, dtype=np.float64)
    f = np.asarray(force_n, dtype=np.float64)
    mask = (r > 0) & (f > 0)
    x = np.log10(r[mask])
    y = np.log10(f[mask])
    if len(x) < 2:
        raise ValueError("need at least two positive (R, F) pairs")
    b, a = np.polyfit(x, y, 1)
    return float(a), float(b)


def calibration_residuals(
    force_true_n: np.ndarray,
    force_pred_n: np.ndarray,
) -> dict[str, float]:
    t = np.asarray(force_true_n, dtype=np.float64)
    p = np.asarray(force_pred_n, dtype=np.float64)
    err = p - t
    mae = float(np.mean(np.abs(err)))
    rmse = float(np.sqrt(np.mean(err**2)))
    max_abs = float(np.max(np.abs(err)))
    denom = np.maximum(np.abs(t), 1e-6)
    mape = float(np.mean(np.abs(err) / denom) * 100.0)
    return {"mae_n": mae, "rmse_n": rmse, "max_abs_n": max_abs, "mape_pct": mape, "n": float(len(t))}


def repeatability_cv(repeated_force_n: np.ndarray) -> float:
    """Coefficient of variation across repeated loads at a fixed condition."""
    x = np.asarray(repeated_force_n, dtype=np.float64)
    mean = float(np.mean(x))
    if mean <= 1e-9:
        return float("nan")
    return float(np.std(x, ddof=1) / mean)


def hysteresis_error(loading_n: np.ndarray, unloading_n: np.ndarray) -> float:
    """Mean absolute loading vs unloading difference (same commanded force grid)."""
    a = np.asarray(loading_n, dtype=np.float64)
    b = np.asarray(unloading_n, dtype=np.float64)
    if a.shape != b.shape:
        raise ValueError("loading and unloading arrays must match")
    return float(np.mean(np.abs(a - b)))


def drift_rate(unloaded_kpa: np.ndarray, sample_hz: float) -> dict[str, float]:
    """Linear drift of an unloaded sensor (kPa / minute)."""
    y = np.asarray(unloaded_kpa, dtype=np.float64)
    t_min = np.arange(len(y)) / max(sample_hz, 1e-6) / 60.0
    if len(y) < 2:
        return {"slope_kpa_per_min": float("nan"), "delta_kpa": 0.0}
    slope, _ = np.polyfit(t_min, y, 1)
    return {"slope_kpa_per_min": float(slope), "delta_kpa": float(y[-1] - y[0])}


def simulate_example_curve(
    cal: SensorCalibration,
    force_n: np.ndarray | None = None,
    noise_adc: float = 8.0,
    seed: int = 67,
) -> dict[str, np.ndarray]:
    """Forward-simulate ADC from a known curve. **Not a lab measurement.**"""
    rng = np.random.default_rng(seed)
    if force_n is None:
        force_n = np.concatenate([np.linspace(0.5, 40.0, 25), np.linspace(40.0, 0.5, 25)])
    force_n = np.asarray(force_n, dtype=np.float64)
    # Invert log-log: R = 10 ** ((log10(F) - a) / b)
    log_r = (np.log10(np.clip(force_n, 1e-3, None)) - cal.loglog_a) / cal.loglog_b
    r = 10.0 ** log_r
    adc_clean = cal.adc_full_scale * cal.r_fixed_ohm / (r + cal.r_fixed_ohm)
    adc = np.clip(adc_clean + rng.normal(0.0, noise_adc, size=adc_clean.shape), 1.0, cal.adc_full_scale)
    pred_r = adc_to_resistance_ohm(adc, cal)
    pred_f = resistance_to_force_n(pred_r, cal)
    pred_p = force_n_to_pressure_kpa(pred_f, cal)
    true_p = force_n_to_pressure_kpa(force_n, cal)
    return {
        "force_true_n": force_n,
        "adc": adc,
        "resistance_ohm": pred_r,
        "force_pred_n": pred_f,
        "pressure_true_kpa": true_p,
        "pressure_pred_kpa": pred_p,
        "direction": np.array(["loading"] * 25 + ["unloading"] * 25),
    }


def write_template_csv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "site,trial,direction,force_n,adc,notes\n"
        "met1,1,loading,,,# fill after bench calibration; do not invent values\n"
    )


def plot_calibration_figures(
    sim: dict[str, np.ndarray],
    residuals: dict[str, float],
    out_dir: Path,
    caption_note: str = "SIMULATED example — not a physical bench measurement",
) -> list[Path]:
    import matplotlib.pyplot as plt

    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    def _save(fig, stem: str) -> None:
        for ext in (".png", ".pdf", ".svg"):
            p = out_dir / f"{stem}{ext}"
            fig.savefig(p, dpi=300, bbox_inches="tight")
            paths.append(p)
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(5.2, 4.0))
    ax.plot(sim["force_true_n"], sim["adc"], ".", alpha=0.7, label="simulated ADC")
    ax.set_xlabel("Commanded force (N)")
    ax.set_ylabel("ADC counts")
    ax.set_title(f"Calibration curve\n{caption_note}")
    ax.legend()
    _save(fig, "fig_calibration_curve")

    fig, ax = plt.subplots(figsize=(5.2, 4.0))
    ax.scatter(sim["force_true_n"], sim["force_pred_n"], s=18, alpha=0.75)
    lim = [0, max(float(sim["force_true_n"].max()), float(sim["force_pred_n"].max()))]
    ax.plot(lim, lim, "k--", lw=1, label="identity")
    ax.set_xlabel("True force (N)")
    ax.set_ylabel("Predicted force (N)")
    ax.set_title(f"Measured vs predicted force\n{caption_note}")
    ax.legend()
    _save(fig, "fig_calibration_measured_vs_pred")

    fig, ax = plt.subplots(figsize=(5.2, 4.0))
    err = sim["force_pred_n"] - sim["force_true_n"]
    ax.scatter(sim["force_pred_n"], err, s=18, alpha=0.75)
    ax.axhline(0.0, color="k", lw=1)
    ax.set_xlabel("Predicted force (N)")
    ax.set_ylabel("Residual (pred − true, N)")
    ax.set_title(f"Residuals (MAE={residuals['mae_n']:.2f} N)\n{caption_note}")
    _save(fig, "fig_calibration_residuals")

    return paths
