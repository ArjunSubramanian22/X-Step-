import numpy as np
import pytest

from xstep_ml.data.synthetic_gait import synthesize_window
from xstep_ml.inference.engine import ProductionEngine
from xstep_ml.models.clinical import ClinicalProfile
from xstep_ml.models.tabular_fusion import UnpairedModalityError, assert_paired, compare_unimodal_vs_fusion


def test_risk_contributions_present(tmp_path):
    engine = ProductionEngine(artifact_dir=tmp_path)
    frames, _, _ = synthesize_window("left_forefoot_overload", np.random.default_rng(4))
    result = engine.analyze_window(frames.tolist(), profile=ClinicalProfile(neuropathy="Moderate"))
    names = {c["name"] for c in result.contributions}
    assert "elevated_forefoot_load" in names
    assert "repeated_peak_pressure" in names
    assert "asymmetry" in names


def test_unpaired_fusion_refused():
    with pytest.raises(UnpairedModalityError):
        assert_paired(np.array(["a", "b"]), np.array(["a", "c"]))
    ids = np.array(["w0", "w1"])
    info = compare_unimodal_vs_fusion(np.zeros((2, 3)), np.zeros((2, 2)), np.array([0, 1]), ids)
    assert "invalid" in info["multimodal_image_plus_pressure"]
