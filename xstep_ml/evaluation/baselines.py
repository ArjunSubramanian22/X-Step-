"""EHB-style experiment helpers: baselines, group CV, ablation, robustness."""

from __future__ import annotations

from sklearn.dummy import DummyClassifier
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC


def baseline_models(random_state: int = 67) -> dict[str, Pipeline]:
    return {
        "majority": Pipeline([("clf", DummyClassifier(strategy="most_frequent"))]),
        "logreg": Pipeline(
            [
                ("scaler", StandardScaler()),
                ("clf", LogisticRegression(max_iter=400, class_weight="balanced", random_state=random_state)),
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
    }


FEATURE_GROUPS = {
    "peak_only": lambda names: [i for i, n in enumerate(names) if n.endswith("_peak") or n in ("peak_any",)],
    "no_asymmetry": lambda names: [i for i, n in enumerate(names) if not n.startswith("asym_")],
    "no_temporal": lambda names: [i for i, n in enumerate(names) if n not in ("cadence_spm", "stance_ratio")],
    "full": lambda names: list(range(len(names))),
}
