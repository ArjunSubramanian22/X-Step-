import numpy as np

from xstep_ml.biomechanics import FEATURE_NAMES, GaitWindow, extract_features
from xstep_ml.data.synthetic_gait import synthesize_window
from xstep_ml.features import EXTENDED_NAMES, FEATURE_SPEC, extended_from_window, extract_extended_features


def test_production_vector_length_stable():
    rng = np.random.default_rng(0)
    frames, _, _ = synthesize_window("normal", rng)
    feats = extract_features(GaitWindow(frames))
    assert len(feats.vector) == len(FEATURE_NAMES) == 59
    for name in FEATURE_NAMES:
        assert name in FEATURE_SPEC
        assert FEATURE_SPEC[name].unit
        assert FEATURE_SPEC[name].definition


def test_extended_features_units_and_coverage():
    rng = np.random.default_rng(2)
    frames, _, _ = synthesize_window("left_heel_overload", rng, seconds=4.0)
    window = GaitWindow(frames, sample_hz=25.0)
    extra = extended_from_window(window)
    for name in EXTENDED_NAMES:
        assert name in extra
        assert np.isfinite(extra[name])
        assert name in FEATURE_SPEC
    vec, names = extract_extended_features(window)
    assert len(vec) == 59 + len(EXTENDED_NAMES)
    assert names[-1] == EXTENDED_NAMES[-1]
    assert extra["contact_duration_s"] >= 0
    assert extra["overload_events"] >= 0
