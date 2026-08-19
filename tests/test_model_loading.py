
import joblib

from xstep_ml.config import ARTIFACT_DIR, GAIT_MODEL_NAME, ZONE_MODEL_NAME
from xstep_ml.data.synthetic_gait import make_cohort
from xstep_ml.models.gait import gait_pipeline


def test_pipeline_fits_and_predicts():
    x, y, _, _ = make_cohort(n_subjects=3, windows_per_class=1, seed=5)
    clf = gait_pipeline().fit(x, y)
    pred = clf.predict(x[:2])
    assert len(pred) == 2


def test_artifact_load_if_present():
    path = ARTIFACT_DIR / GAIT_MODEL_NAME
    zone = ARTIFACT_DIR / ZONE_MODEL_NAME
    if not path.exists():
        return
    model = joblib.load(path)
    x, y, _, _ = make_cohort(n_subjects=2, windows_per_class=1, seed=5)
    model.predict(x[:1])
    if zone.exists():
        joblib.load(zone)
