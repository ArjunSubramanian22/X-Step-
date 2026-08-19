#!/usr/bin/env python3
"""Train production 4-FSR gait + high-risk-zone models and write artifacts."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import joblib
import numpy as np
from sklearn.metrics import classification_report

from xstep_ml.biomechanics import GaitWindow, extract_features
from xstep_ml.config import ARTIFACT_DIR, GAIT_MODEL_NAME, PRODUCTION_MANIFEST, ZONE_MODEL_NAME
from xstep_ml.data.synthetic_gait import make_cohort, synthesize_window
from xstep_ml.evaluation.splits import grouped_train_test_split
from xstep_ml.models.gait import gait_pipeline, zone_pipeline


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    x, y_gait, y_zone, groups = make_cohort(n_subjects=24, windows_per_class=12, seed=67)
    tr, te = grouped_train_test_split(x, y_gait, groups, test_size=0.2, random_state=67, kind="subject")
    x_tr, x_te = x[tr], x[te]
    g_tr, g_te = y_gait[tr], y_gait[te]
    z_tr, z_te = y_zone[tr], y_zone[te]

    gait = gait_pipeline()
    gait.fit(x_tr, g_tr)
    zone = zone_pipeline()
    zone.fit(x_tr, z_tr)

    gait_pred = gait.predict(x_te)
    zone_pred = zone.predict(x_te)
    gait_report = classification_report(g_te, gait_pred, output_dict=True, zero_division=0)
    zone_report = classification_report(z_te, zone_pred, output_dict=True, zero_division=0)

    joblib.dump(gait, ARTIFACT_DIR / GAIT_MODEL_NAME)
    joblib.dump(zone, ARTIFACT_DIR / ZONE_MODEL_NAME)

    sample_frames, _, _ = synthesize_window("normal", np.random.default_rng(0))
    names = extract_features(GaitWindow(sample_frames)).names

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "gait_model": GAIT_MODEL_NAME,
        "zone_model": ZONE_MODEL_NAME,
        "n_train": int(len(x_tr)),
        "n_test": int(len(x_te)),
        "gait_accuracy": gait_report["accuracy"],
        "zone_accuracy": zone_report["accuracy"],
        "gait_macro_f1": gait_report["macro avg"]["f1-score"],
        "zone_macro_f1": zone_report["macro avg"]["f1-score"],
        "feature_names": names,
        "sample_hz": 25,
        "channels": 8,
        "n_subjects": int(len(np.unique(groups))),
        "eval_note": "Subject-grouped hold-out for the shipped artifact. Paper tables use GroupKFold from research/experiments/run_research.py. Synthetic data only.",
        "sites": ["met1", "met2", "met5", "heel"],
    }
    with open(ARTIFACT_DIR / PRODUCTION_MANIFEST, "w") as f:
        json.dump(manifest, f, indent=2)
    with open(ARTIFACT_DIR / "gait_report.json", "w") as f:
        json.dump(gait_report, f, indent=2)
    with open(ARTIFACT_DIR / "zone_report.json", "w") as f:
        json.dump(zone_report, f, indent=2)

    print(json.dumps({k: manifest[k] for k in ("gait_accuracy", "zone_accuracy", "gait_macro_f1", "zone_macro_f1")}, indent=2))


if __name__ == "__main__":
    main()
