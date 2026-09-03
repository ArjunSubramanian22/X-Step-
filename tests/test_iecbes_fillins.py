"""Lock IECBES fill-in arithmetic to frozen ablation and calibration artefacts."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from research.experiments.iecbes_fillins import (
    HY,
    fano_pack,
    interactions,
    layout_value_map,
    shapley_from_v,
)

ROOT = Path(__file__).resolve().parents[1]


def test_best_two_site_is_met2_heel():
    inter = interactions(layout_value_map())
    assert inter["best_two_site"]["sites"] == ["HEEL", "MET2"]
    assert abs(inter["best_two_site"]["macro_f1"] - 0.686) < 5e-4


def test_shapley_sums_to_total_value():
    v = layout_value_map()
    phi = shapley_from_v(v)
    total = v[frozenset(("MET1", "MET2", "MET5", "HEEL"))] - v[frozenset()]
    assert abs(sum(phi.values()) - total) < 1e-12
    assert abs(phi["MET1"] - 0.152) < 5e-4
    assert abs(phi["HEEL"] - 0.280) < 5e-4


def test_met1_met2_interaction_uses_met5_heel_complement():
    inter = interactions(layout_value_map())
    pair = inter["I_MET1_MET2"]
    assert pair["complement"] == ["HEEL", "MET5"]
    assert abs(pair["I"] - 0.223) < 5e-3


def test_fano_dummy_at_one_ninth_is_zero():
    pack = fano_pack(1.0 / 9.0)
    assert pack["I_lower"] == 0.0
    assert abs(HY - math.log2(9)) < 1e-12


def test_production_fano_matches_paper():
    pack = fano_pack(0.8850308641975309)
    assert abs(pack["I_lower"] - 2.310) < 5e-4
    assert abs(pack["pct_of_HY"] - 72.9) < 0.05


def test_official_calibration_k_b():
    cal = json.loads((ROOT / "research/results/calibration_evaluation.json").read_text())
    by_site = {row["site"]: row for row in cal["per_site"]}
    k_met1 = 10.0 ** by_site["met1"]["loglog_a"]
    assert abs(k_met1 / 1.74e5 - 1.0) < 0.01
    assert abs(by_site["met1"]["loglog_b"] + 1.212) < 5e-3


def test_fillins_json_records_cluster_ci_and_tost():
    payload = json.loads((ROOT / "research/results/iecbes_fillins.json").read_text())
    ci = payload["cluster_bootstrap_logreg"]
    assert ci["ci95_lo"] < 0.873  # wider than the window-level interval
    assert ci["ci95_hi"] > 0.894
    tost = payload["tost_logreg_vs_hist_gbm"]
    assert tost["equivalent"] is True
    assert tost["ci90_lo"] > -0.02
    assert tost["ci90_hi"] < 0.02
    assert payload["holm_vs_dummy"]["p_holm"]["logreg"] < 0.005
