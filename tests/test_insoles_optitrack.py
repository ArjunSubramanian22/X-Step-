import json
from pathlib import Path

import numpy as np

from research.insoles_optitrack import (
    evaluate_arrays,
    four_site_series,
    icc_oneway,
    load_layout,
    pearson,
    region_max_series,
)


def test_layout_has_four_sites_and_32_channels():
    layout = load_layout()
    assert layout["not_xstep_4fsr"] is True
    for side in ("left", "right"):
        for site in ("met1", "met2", "met5", "heel"):
            spec = layout["sides"][side][site]
            assert 0 <= spec["representative"] <= 31
            assert spec["representative"] in spec["members"]
            assert all(0 <= i <= 31 for i in spec["members"])


def test_sparse_site_is_not_identically_region_max():
    layout = load_layout()
    rng = np.random.default_rng(7)
    t = np.linspace(0, 4 * np.pi, 100)
    arr = 20 + rng.normal(0, 2, (100, 32))
    arr[:, 7] += 40 * (np.sin(t) > 0)
    arr[:, 20] += 35 * (np.sin(t + 0.4) > 0)
    arr[:, 10] += 30 * (np.sin(t + 0.8) > 0)
    arr[:, 30] += 50 * (np.sin(t + 1.2) > 0)
    # another member of heel is even larger — dense max != representative
    arr[:, 31] += 80 * (np.sin(t + 1.2) > 0)
    four = four_site_series(arr, layout)
    dense = region_max_series(arr, layout)
    assert float(np.max(dense["heel"])) > float(np.max(four["heel"]))
    out = evaluate_arrays(arr, arr, layout=layout)
    assert out["not_xstep_four_site_fsr"] is True
    assert out["sides"][0]["met1_r"] > 0.9


def test_icc_perfect_and_noise():
    perfect = np.array(
        [
            [10.0, 10.0, 10.0],
            [20.0, 20.0, 20.0],
            [30.0, 30.0, 30.0],
            [40.0, 40.0, 40.0],
        ]
    )
    assert icc_oneway(perfect) > 0.99
    noisy = perfect + np.array(
        [
            [0.0, 8.0, -7.0],
            [0.0, -9.0, 6.0],
            [0.0, 7.0, -8.0],
            [0.0, -6.0, 9.0],
        ]
    )
    assert icc_oneway(noisy) < icc_oneway(perfect)


def test_pearson_rejects_tiny_series():
    a = np.arange(3.0)
    assert np.isnan(pearson(a, a))


def test_evaluation_json_does_not_claim_xstep_fsr():
    path = Path(__file__).resolve().parents[1] / "research" / "results" / "human_optitrack_evaluation.json"
    if not path.exists():
        return
    payload = json.loads(path.read_text())
    assert payload["not_xstep_four_site_fsr"] is True
    assert payload["data_source"] == "human"
    assert payload["n_subjects"] == 15
    assert payload["n_takes_analyzed"] == 149
    assert payload["median_copy_r"] > 0.7
    assert "not X-Step" in payload["hardware"]
    assert "subject_codes" not in payload.get("demographics_aggregate", {})
