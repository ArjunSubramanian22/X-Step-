import numpy as np
import pytest
from sklearn.model_selection import train_test_split

from xstep_ml.evaluation.splits import LeakageError, assert_no_group_overlap, grouped_train_test_split


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
