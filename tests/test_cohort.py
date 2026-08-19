import numpy as np

from xstep_ml.data.synthetic_gait import make_cohort
from xstep_ml.models.gait import GAIT_CLASSES


def test_cohort_grouped_shape():
    x, y_gait, y_zone, sid = make_cohort(n_subjects=4, windows_per_class=2, seed=1)
    assert x.shape[0] == 4 * len(GAIT_CLASSES) * 2
    assert len(np.unique(sid)) == 4
    assert set(np.unique(sid)) == {0, 1, 2, 3}
