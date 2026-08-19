import numpy as np

from xstep_ml.evaluation.perturbations import dropped_packets, gaussian_noise, mask_sites, missing_sensor


def test_perturbations_preserve_shape():
    rng = np.random.default_rng(0)
    w = rng.random((5, 20, 8)) * 40
    assert gaussian_noise(w, rng, 3.0).shape == w.shape
    assert dropped_packets(w, rng, 0.2).shape == w.shape
    m = missing_sensor(w, 1)
    assert np.allclose(m[:, :, 1], 0)
    assert np.allclose(m[:, :, 5], 0)
    keep = mask_sites(w, [3])
    assert np.allclose(keep[:, :, 0], 0)
    assert keep[:, :, 3].sum() > 0
