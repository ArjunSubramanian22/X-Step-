import numpy as np

from xstep_ml.calibration import (
    SensorCalibration,
    adc_to_pressure_kpa,
    adc_to_resistance_ohm,
    calibration_residuals,
    drift_rate,
    hysteresis_error,
    repeatability_cv,
    simulate_example_curve,
)


def test_linear_adc_map():
    cal = SensorCalibration(site="met1", model="linear_adc", kpa_full_scale=250.0, adc_full_scale=4095.0)
    p = float(adc_to_pressure_kpa(4095, cal))
    assert abs(p - 250.0) < 1e-6


def test_divider_resistance_monotonic():
    cal = SensorCalibration(site="heel")
    r_lo = float(adc_to_resistance_ohm(3000, cal))
    r_hi = float(adc_to_resistance_ohm(500, cal))
    assert r_hi > r_lo


def test_simulated_residuals_finite():
    cal = SensorCalibration(site="met2", model="loglog")
    sim = simulate_example_curve(cal, seed=1)
    res = calibration_residuals(sim["force_true_n"], sim["force_pred_n"])
    assert np.isfinite(res["mae_n"])
    assert res["n"] > 10


def test_repeatability_and_hysteresis():
    x = np.array([10.0, 10.2, 9.8, 10.1])
    assert repeatability_cv(x) < 0.05
    assert hysteresis_error(np.array([1.0, 2.0]), np.array([1.1, 2.2])) > 0
    d = drift_rate(np.linspace(0, 2, 50), sample_hz=25.0)
    assert d["slope_kpa_per_min"] > 0
