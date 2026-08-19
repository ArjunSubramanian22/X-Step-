import json
from pathlib import Path

import numpy as np
import pytest
from sklearn.model_selection import GroupKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from xstep_ml.data.synthetic_gait import make_cohort
from xstep_ml.evaluation.baselines import baseline_models
from xstep_ml.evaluation.splits import LeakageError, assert_no_group_overlap, grouped_train_test_split

ROOT = Path(__file__).resolve().parents[1]
SPLITS = ROOT / "research" / "results" / "splits"


def test_grouped_split_no_subject_overlap():
    rng = np.random.default_rng(0)
    X = rng.normal(size=(40, 3))
    y = rng.integers(0, 2, size=40)
    groups = np.repeat(np.arange(8), 5)
    tr, te = grouped_train_test_split(X, y, groups, test_size=0.25, random_state=0)
    assert set(groups[tr]).isdisjoint(set(groups[te]))


def test_detects_iid_window_leakage():
    groups = np.array([0, 0, 1, 1, 2, 2])
    idx = np.arange(len(groups))
    tr, te = train_test_split(idx, test_size=0.5, random_state=0)
    with pytest.raises(LeakageError):
        assert_no_group_overlap(groups[tr], groups[te], kind="subject")


def test_frozen_subject_folds_have_disjoint_indices_and_subjects():
    path = SPLITS / "subject_groupkfold.json"
    if not path.exists():
        pytest.skip("frozen split dump missing")
    payload = json.loads(path.read_text())
    _x, _y, _z, subject_id = make_cohort(n_subjects=24, windows_per_class=12, seed=67)
    assert len(subject_id) == payload["n_examples"]
    for fold in payload["folds"]:
        tr = np.asarray(fold["train_idx"])
        te = np.asarray(fold["test_idx"])
        assert set(tr).isdisjoint(set(te))
        assert_no_group_overlap(subject_id[tr], subject_id[te], kind="subject")


def test_frozen_session_folds_have_disjoint_indices():
    path = SPLITS / "session_groupkfold.json"
    if not path.exists():
        pytest.skip("frozen session split dump missing")
    payload = json.loads(path.read_text())
    for fold in payload["folds"]:
        tr = set(fold["train_idx"])
        te = set(fold["test_idx"])
        assert tr.isdisjoint(te)


def test_no_exact_duplicate_windows_across_subject_holdout():
    X, y, _z, groups = make_cohort(n_subjects=8, windows_per_class=2, seed=67)
    gkf = GroupKFold(n_splits=4)
    for tr, te in gkf.split(X, y, groups):
        assert_no_group_overlap(groups[tr], groups[te], kind="subject")
        train_hashes = {row.tobytes() for row in np.round(X[tr], 6)}
        leak = sum(1 for row in np.round(X[te], 6) if row.tobytes() in train_hashes)
        assert leak == 0


def test_scaler_must_not_be_fit_on_full_dataset_before_split():
    """Guardrail: fitting StandardScaler on all rows before grouping is leakage."""
    X, y, _z, groups = make_cohort(n_subjects=6, windows_per_class=2, seed=0)
    tr, te = grouped_train_test_split(X, y, groups, test_size=0.3, random_state=0)
    pipe = Pipeline([("scaler", StandardScaler())])
    pipe.fit(X[tr])
    mean_train = pipe.named_steps["scaler"].mean_
    leaked = StandardScaler().fit(X)
    assert not np.allclose(mean_train, leaked.mean_), "full-data scaler should differ from train-only scaler"


def test_hyperparameters_are_a_priori_not_test_tuned():
    models = baseline_models(random_state=67)
    clf = models["logreg"].named_steps["clf"]
    assert clf.max_iter == 400
    assert clf.class_weight == "balanced"
    assert "X_test" not in baseline_models.__code__.co_varnames
