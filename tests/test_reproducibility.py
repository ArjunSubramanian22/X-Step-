import numpy as np

from xstep_ml.data.schema import dataset_hash
from xstep_ml.data.synthetic_gait import make_cohort
from xstep_ml.models.gait import gait_pipeline
from xstep_ml.reproducibility import environment_record


def test_same_seed_same_cohort_hash():
    a = make_cohort(n_subjects=3, windows_per_class=1, seed=11)
    b = make_cohort(n_subjects=3, windows_per_class=1, seed=11)
    assert dataset_hash(a[0], a[1], a[3]) == dataset_hash(b[0], b[1], b[3])
    np.testing.assert_allclose(a[0], b[0])


def test_model_predict_deterministic():
    x, y, _, _ = make_cohort(n_subjects=4, windows_per_class=2, seed=3)
    m1 = gait_pipeline().fit(x, y)
    m2 = gait_pipeline().fit(x, y)
    assert list(m1.predict(x[:8])) == list(m2.predict(x[:8]))


def test_environment_record_has_python():
    rec = environment_record()
    assert rec["python"]
    assert "git_sha" in rec
