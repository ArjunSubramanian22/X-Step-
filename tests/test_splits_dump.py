import numpy as np

from xstep_ml.evaluation.splits import dump_split_definitions, grouped_train_test_split, leave_one_subject_out


def test_dump_and_loso(tmp_path):
    groups = np.repeat(np.arange(6), 4)
    y = np.tile([0, 1], 12)
    X = np.zeros((len(groups), 2))
    tr, te = grouped_train_test_split(X, y, groups, test_size=0.3, random_state=0)
    path = tmp_path / "split.json"
    dump_split_definitions(path, [(tr, te)], groups, protocol="subject", y=y)
    payload = path.read_text()
    assert "train_idx" in payload
    folds = leave_one_subject_out(groups)
    assert len(folds) == 6
