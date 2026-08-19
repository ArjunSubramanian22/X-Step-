"""EHB-style experiment helpers: baselines, group CV, ablation, robustness."""

from __future__ import annotations

import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import GradientBoostingClassifier, HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC
from sklearn.tree import DecisionTreeClassifier


class ThresholdHeuristicClassifier(BaseEstimator, ClassifierMixin):
    """Rule-based overload localization from peak/cadence features.

    Engineering baseline, not a clinical rule.
    """

    def __init__(
        self,
        feature_names: list[str] | None = None,
        peak_normal_kpa: float = 70.0,
        shuffle_cadence: float = 88.0,
        asym_cut: float = 0.42,
    ):
        self.feature_names = feature_names
        self.peak_normal_kpa = peak_normal_kpa
        self.shuffle_cadence = shuffle_cadence
        self.asym_cut = asym_cut

    def fit(self, X, y):
        self.classes_ = np.unique(y)
        self.n_features_in_ = np.asarray(X).shape[1]
        return self

    def _idx(self) -> dict[str, int]:
        names = self.feature_names or []
        return {n: i for i, n in enumerate(names)}

    def predict(self, X):
        X = np.asarray(X, dtype=np.float64)
        idx = self._idx()
        out = []
        for row in X:
            out.append(self._predict_row(row, idx))
        return np.asarray(out, dtype=object)

    def _predict_row(self, row: np.ndarray, idx: dict[str, int]) -> str:
        def g(name: str, default: float = 0.0) -> float:
            i = idx.get(name)
            return float(row[i]) if i is not None and i < len(row) else default

        cadence = g("cadence_spm")
        scores = {
            "left_forefoot_overload": g("L_met1_peak") + g("L_met2_peak"),
            "right_forefoot_overload": g("R_met1_peak") + g("R_met2_peak"),
            "left_heel_overload": g("L_heel_peak"),
            "right_heel_overload": g("R_heel_peak"),
            "left_lateral_overload": g("L_met5_peak"),
            "right_lateral_overload": g("R_met5_peak"),
        }
        best_label = max(scores, key=scores.get)
        best_val = scores[best_label]
        l_sum = g("L_met1_peak") + g("L_met2_peak") + g("L_met5_peak") + g("L_heel_peak")
        r_sum = g("R_met1_peak") + g("R_met2_peak") + g("R_met5_peak") + g("R_heel_peak")
        asym = abs(l_sum - r_sum) / max((l_sum + r_sum) / 2.0, 1e-3)
        if cadence and cadence < self.shuffle_cadence and best_val < self.peak_normal_kpa * 1.4:
            return "shuffling_low_cadence"
        if asym > self.asym_cut and best_val < self.peak_normal_kpa * 1.6:
            return "asymmetric_antalgic"
        if best_val < self.peak_normal_kpa:
            return "normal"
        return best_label


def baseline_models(random_state: int = 67) -> dict[str, Pipeline]:
    return {
        "threshold_heuristic": Pipeline([("clf", ThresholdHeuristicClassifier())]),
        "majority": Pipeline([("clf", DummyClassifier(strategy="most_frequent"))]),
        "logreg": Pipeline(
            [
                ("scaler", StandardScaler()),
                ("clf", LogisticRegression(max_iter=400, class_weight="balanced", random_state=random_state)),
            ]
        ),
        "decision_tree": Pipeline(
            [
                (
                    "clf",
                    DecisionTreeClassifier(
                        max_depth=8,
                        min_samples_leaf=6,
                        class_weight="balanced",
                        random_state=random_state,
                    ),
                )
            ]
        ),
        "linear_svm": Pipeline(
            [
                ("scaler", StandardScaler()),
                ("clf", LinearSVC(class_weight="balanced", random_state=random_state, dual=False, max_iter=4000)),
            ]
        ),
        "random_forest": Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "clf",
                    RandomForestClassifier(
                        n_estimators=160,
                        max_depth=12,
                        min_samples_leaf=4,
                        class_weight="balanced",
                        random_state=random_state,
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
        "gbm": Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "clf",
                    GradientBoostingClassifier(
                        n_estimators=80,
                        max_depth=3,
                        learning_rate=0.08,
                        random_state=random_state,
                    ),
                ),
            ]
        ),
        "mlp": Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "clf",
                    MLPClassifier(
                        hidden_layer_sizes=(64, 32),
                        max_iter=250,
                        random_state=random_state,
                        early_stopping=True,
                    ),
                ),
            ]
        ),
        "hist_gbm": Pipeline(
            [
                (
                    "clf",
                    HistGradientBoostingClassifier(
                        max_depth=3,
                        learning_rate=0.08,
                        max_iter=80,
                        random_state=random_state,
                    ),
                )
            ]
        ),
    }


FEATURE_GROUPS = {
    "peak_only": lambda names: [i for i, n in enumerate(names) if n.endswith("_peak") or n in ("peak_any",)],
    "raw_pressure": lambda names: [
        i for i, n in enumerate(names) if n.endswith("_peak") or n.endswith("_mean") or n in ("peak_any", "cop_ap", "forefoot_share")
    ],
    "temporal": lambda names: [
        i
        for i, n in enumerate(names)
        if n.endswith("_load") or n.endswith("_cv") or n.endswith("_high") or n in ("cadence_spm", "stance_ratio")
    ],
    "pti": lambda names: [i for i, n in enumerate(names) if n.endswith("_pti") or n in ("pti_total",) or n.endswith("_high")],
    "symmetry": lambda names: [i for i, n in enumerate(names) if n.startswith("asym_")],
    "no_asymmetry": lambda names: [i for i, n in enumerate(names) if not n.startswith("asym_")],
    "no_temporal": lambda names: [i for i, n in enumerate(names) if n not in ("cadence_spm", "stance_ratio")],
    "full": lambda names: list(range(len(names))),
}
