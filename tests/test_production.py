"""Unit tests for protocol, biomechanics, and production engine."""

from __future__ import annotations

import numpy as np

from xstep_ml.biomechanics import GaitWindow, extract_features
from xstep_ml.data.synthetic_gait import synthesize_window
from xstep_ml.hardware import adc_to_kpa, kpa_to_adc
from xstep_ml.inference.engine import ProductionEngine
from xstep_ml.models.clinical import ClinicalProfile, iwgdf_risk_category
from xstep_ml.protocol import decode_packet, encode_packet


def test_adc_roundtrip():
    assert abs(adc_to_kpa(kpa_to_adc(100)) - 100) < 0.2


def test_packet_roundtrip():
    raw = encode_packet("left", 42, 1234, (100, 200, 300, 400), 88, temperatures_c=(31.2, 32.0, 31.5, 33.1))
    pkt = decode_packet(raw)
    assert pkt.side == "left"
    assert pkt.seq == 42
    assert pkt.battery == 88
    assert pkt.temperatures_c is not None
    assert abs(pkt.temperatures_c[0] - 31.2) < 0.05


def test_features_shape():
    rng = np.random.default_rng(0)
    frames, _, _ = synthesize_window("left_heel_overload", rng)
    feats = extract_features(GaitWindow(frames))
    assert feats.vector.ndim == 1
    assert feats.extras["peak_any"] > 40


def test_iwgdf_high_risk():
    assert iwgdf_risk_category(ClinicalProfile(prior_ulcer=True)) == 3
    assert iwgdf_risk_category(ClinicalProfile(neuropathy="None")) == 0


def test_engine_runs_without_artifacts(tmp_path):
    engine = ProductionEngine(artifact_dir=tmp_path)
    rng = np.random.default_rng(1)
    frames, _, _ = synthesize_window("left_forefoot_overload", rng)
    result = engine.analyze_window(frames.tolist(), profile=ClinicalProfile(neuropathy="Moderate", hba1c=8.2))
    assert 0 <= result.health_index <= 100
    assert result.level in ("green", "amber", "red")
    assert result.extras["peak_any"] > 0
