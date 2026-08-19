import numpy as np

from xstep_ml.evaluation.stats import coefficient_of_variation, icc_1_1, mean_absolute_deviation


def test_cv_and_mad():
    x = np.array([10.0, 10.0, 10.0])
    assert coefficient_of_variation(x) == 0.0
    assert mean_absolute_deviation(x) == 0.0


def test_icc_perfect_agreement():
    ratings = np.array([[1.0, 1.0], [2.0, 2.0], [3.0, 3.0], [4.0, 4.0]])
    assert icc_1_1(ratings) > 0.99
