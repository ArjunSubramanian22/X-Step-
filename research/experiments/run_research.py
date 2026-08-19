#!/usr/bin/env python3
"""Engineering/simulation experiments for the EHB research pipeline.

Data source is the in-silico 4-FSR cohort unless a future human loader is wired
into `make_cohort_bundle` with the same return type. Results files always record
`data_source` and `validation_type`.
"""

from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("MPLCONFIGDIR", str(_ROOT / ".mplconfig"))
(_ROOT / ".mplconfig").mkdir(exist_ok=True)

import numpy as np
from sklearn.base import clone
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import GroupKFold

if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from xstep_ml.biomechanics import GaitWindow, extract_features
from xstep_ml.calibration import (
    SensorCalibration,
    calibration_residuals,
    plot_calibration_figures,
    simulate_example_curve,
    write_template_csv,
)
from xstep_ml.data.schema import PressureWindowRecord, dataset_hash, validate_records
from xstep_ml.data.synthetic_gait import CohortBundle, make_cohort_bundle
from xstep_ml.evaluation.baselines import ThresholdHeuristicClassifier, baseline_models
from xstep_ml.evaluation.efficiency import model_efficiency_row
from xstep_ml.evaluation.perturbations import (
    SENSOR_SUBSETS,
    calibration_drift,
    dropped_packets,
    gaussian_noise,
    mask_sites,
    missing_sensor,
    resample_to_length,
    sensor_bias,
    short_dropout,
    subset_label,
    timing_jitter,
)
from xstep_ml.evaluation.publication import bootstrap_macro_f1, classification_suite
from xstep_ml.evaluation.splits import assert_no_group_overlap, grouped_train_test_split
from xstep_ml.evaluation.stats import mcnemar_b
from xstep_ml.hardware import ALERT_PRESSURE_KPA
from xstep_ml.models.gait import GAIT_CLASSES, gait_pipeline, save_artifact, zone_pipeline
from xstep_ml.protocol import decode_packet, encode_packet
from xstep_ml.reproducibility import environment_record, write_manifest

RES = _ROOT / "research" / "results"
TAB = _ROOT / "research" / "tables"
FIG = _ROOT / "research" / "figures"
CAL = _ROOT / "data" / "calibration"


def _cfg() -> dict:
    smoke = os.environ.get("RESEARCH_SMOKE", "0") == "1"
    if smoke:
        return {
            "name": "smoke",
            "n_subjects": 6,
            "windows_per_class": 2,
            "n_splits": 3,
            "n_boot": 20,
            "seed": 67,
            "hz": 25.0,
            "seconds": 4.0,
            "noise_std": 3.5,
            "label_noise": 0.03,
            "models": ["threshold_heuristic", "majority", "logreg", "decision_tree", "random_forest"],
            "latency_repeats": 15,
        }
    return {
        "name": "full",
        "n_subjects": 24,
        "windows_per_class": 12,
        "n_splits": 5,
        "n_boot": int(os.environ.get("BOOTSTRAP_N", "400")),
        "seed": 67,
        "hz": 25.0,
        "seconds": 4.0,
        "noise_std": 3.5,
        "label_noise": 0.03,
        "models": list(baseline_models().keys()),
        "latency_repeats": 40,
    }


def _write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return
    keys = fieldnames or list(rows[0].keys())
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in keys})


def _json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, default=str))


def _features(windows: np.ndarray, hz: float) -> np.ndarray:
    rows = [extract_features(GaitWindow(w, sample_hz=hz)).vector for w in windows]
    return np.vstack(rows)


def _prepare_model(name: str, proto, feature_names: list[str]):
    model = clone(proto)
    clf = model.named_steps.get("clf")
    if isinstance(clf, ThresholdHeuristicClassifier):
        clf.feature_names = list(feature_names)
    return model


def group_cv_oof(model_name: str, proto, X, y, groups, names, n_splits: int, seed: int):
    n_groups = len(np.unique(groups))
    splits = min(n_splits, n_groups)
    gkf = GroupKFold(n_splits=splits)
    oof = np.empty(len(y), dtype=object)
    label_order = [str(c) for c in GAIT_CLASSES]
    oof_proba = None
    fold_rows = []
    for fold, (tr, te) in enumerate(gkf.split(X, y, groups), 1):
        assert_no_group_overlap(groups[tr], groups[te], kind="subject")
        clf = _prepare_model(model_name, proto, names)
        clf.fit(X[tr], y[tr])
        pred = clf.predict(X[te])
        oof[te] = pred
        if hasattr(clf, "predict_proba"):
            try:
                raw_p = np.asarray(clf.predict_proba(X[te]), dtype=np.float64)
                aligned = np.zeros((len(te), len(label_order)), dtype=np.float64)
                classes = [str(c) for c in clf.classes_]
                for j, lab in enumerate(classes):
                    if lab in label_order:
                        aligned[:, label_order.index(lab)] = raw_p[:, j]
                if oof_proba is None:
                    oof_proba = np.full((len(y), len(label_order)), np.nan)
                oof_proba[te] = aligned
            except Exception:
                pass
        fold_rows.append(
            {
                "fold": fold,
                "accuracy": float(accuracy_score(y[te], pred)),
                "macro_f1": float(f1_score(y[te], pred, average="macro", zero_division=0)),
                "n_test": int(len(te)),
            }
        )
    return oof.astype(str), oof_proba, fold_rows, label_order


def run_baselines(bundle: CohortBundle, cfg: dict) -> tuple[list[dict], dict[str, np.ndarray], dict]:
    models = baseline_models(cfg["seed"])
    keep = cfg["models"]
    table = []
    oof_store = {}
    extra = {}
    names = bundle.feature_names
    for name in keep:
        proto = models[name]
        oof, proba, folds, classes = group_cv_oof(
            name, proto, bundle.X, bundle.y_gait, bundle.subject_id, names, cfg["n_splits"], cfg["seed"]
        )
        oof_store[name] = oof
        f1 = bootstrap_macro_f1(bundle.y_gait, oof, n_boot=cfg["n_boot"], seed=cfg["seed"])
        suite = classification_suite(bundle.y_gait, oof, proba, labels=list(GAIT_CLASSES))
        table.append(
            {
                "model": name,
                "data_source": bundle.data_source,
                "validation_type": "engineering_simulation",
                "split": "GroupKFold-subject",
                "accuracy": suite["accuracy"],
                "balanced_accuracy": suite["balanced_accuracy"],
                "precision_macro": suite["precision_macro"],
                "recall_macro": suite["recall_macro"],
                "specificity_macro": suite["specificity_macro"],
                "macro_f1": suite["macro_f1"],
                "weighted_f1": suite["weighted_f1"],
                "macro_f1_ci95_lo": f1["ci95_lo"],
                "macro_f1_ci95_hi": f1["ci95_hi"],
                "auroc_macro": suite.get("auroc_macro"),
                "pr_auc_macro": suite.get("pr_auc_macro"),
                "brier": suite.get("brier"),
                "ece": (suite.get("calibration") or {}).get("ece") if isinstance(suite.get("calibration"), dict) else None,
                "fold_macro_f1_mean": float(np.mean([r["macro_f1"] for r in folds])),
                "fold_macro_f1_std": float(np.std([r["macro_f1"] for r in folds])),
                "n_windows": int(len(bundle.y_gait)),
                "n_subjects": int(len(np.unique(bundle.subject_id))),
            }
        )
        extra[name] = {"per_class": suite["per_class"], "confusion_matrix": suite["confusion_matrix"], "labels": suite["labels"]}
    return table, oof_store, extra


def run_sensor_ablation(bundle: CohortBundle, cfg: dict) -> list[dict]:
    proto = baseline_models(cfg["seed"])["logreg"]
    rows = []
    for key, keep in SENSOR_SUBSETS.items():
        masked = mask_sites(bundle.windows, keep)
        X = _features(masked, bundle.sample_hz)
        oof, _, folds, _ = group_cv_oof(
            "logreg", proto, X, bundle.y_gait, bundle.subject_id, bundle.feature_names, cfg["n_splits"], cfg["seed"]
        )
        f1 = bootstrap_macro_f1(bundle.y_gait, oof, n_boot=cfg["n_boot"], seed=cfg["seed"])
        rows.append(
            {
                "subset": key,
                "label": subset_label(key),
                "n_sites": len(keep),
                "macro_f1": f1["mean"],
                "macro_f1_ci95_lo": f1["ci95_lo"],
                "macro_f1_ci95_hi": f1["ci95_hi"],
                "fold_macro_f1_mean": float(np.mean([r["macro_f1"] for r in folds])),
                "data_source": bundle.data_source,
                "validation_type": "engineering_simulation",
            }
        )
    return rows


def run_feature_ablation(bundle: CohortBundle, cfg: dict) -> list[dict]:
    from xstep_ml.evaluation.baselines import FEATURE_GROUPS

    proto = baseline_models(cfg["seed"])["logreg"]
    names = bundle.feature_names
    rows = []
    for gname, selector in FEATURE_GROUPS.items():
        idx = selector(names)
        if not idx:
            continue
        oof, _, folds, _ = group_cv_oof(
            "logreg", proto, bundle.X[:, idx], bundle.y_gait, bundle.subject_id, names, cfg["n_splits"], cfg["seed"]
        )
        f1 = bootstrap_macro_f1(bundle.y_gait, oof, n_boot=cfg["n_boot"], seed=cfg["seed"])
        rows.append(
            {
                "feature_set": gname,
                "n_features": len(idx),
                "macro_f1": f1["mean"],
                "macro_f1_ci95_lo": f1["ci95_lo"],
                "macro_f1_ci95_hi": f1["ci95_hi"],
                "data_source": bundle.data_source,
                "validation_type": "engineering_simulation",
            }
        )
    return rows


def run_robustness(bundle: CohortBundle, cfg: dict) -> list[dict]:
    rng = np.random.default_rng(cfg["seed"] + 9)
    tr, te = grouped_train_test_split(bundle.X, bundle.y_gait, bundle.subject_id, test_size=0.25, random_state=cfg["seed"])
    clf = _prepare_model("logreg", baseline_models(cfg["seed"])["logreg"], bundle.feature_names)
    clf.fit(bundle.X[tr], bundle.y_gait[tr])
    test_w = bundle.windows[te]
    y_te = bundle.y_gait[te]
    hz = bundle.sample_hz
    rows = []

    def eval_windows(tag: str, severity: float, windows: np.ndarray) -> None:
        X = _features(windows, hz)
        pred = clf.predict(X)
        rows.append(
            {
                "perturbation": tag,
                "severity": severity,
                "macro_f1": float(f1_score(y_te, pred, average="macro", zero_division=0)),
                "accuracy": float(accuracy_score(y_te, pred)),
                "data_source": bundle.data_source,
                "validation_type": "engineering_simulation",
            }
        )

    eval_windows("none", 0.0, test_w)
    for s in (1.5, 3.5, 7.0, 12.0):
        eval_windows("gaussian_noise_kpa", s, gaussian_noise(test_w, rng, s))
    for s in (0.05, 0.15, 0.30):
        eval_windows("calibration_drift_gain", s, calibration_drift(test_w, rng, s))
    for s in (0.01, 0.05, 0.10, 0.20, 0.30):
        eval_windows("dropped_packets_frac", s, dropped_packets(test_w, rng, s))
    for site in (0, 1, 2, 3):
        eval_windows("missing_sensor_index", float(site), missing_sensor(test_w, site))
    for length in (2, 5, 12):
        eval_windows("short_dropout_samples", float(length), short_dropout(test_w, rng, length))
    for b in (5.0, 15.0, 30.0):
        eval_windows("sensor_bias_kpa", b, sensor_bias(test_w, b))
    for fac in (1, 2, 4):
        ds = test_w[:, ::fac, :]
        rec = resample_to_length(ds, test_w.shape[1])
        eval_windows("sampling_rate_factor", float(fac), rec)
    for j in (0.0, 0.15, 0.35):
        eval_windows("timing_jitter_frac", j, timing_jitter(test_w, rng, j))
    return rows


def run_window_fs(cfg: dict) -> list[dict]:
    proto = baseline_models(cfg["seed"])["logreg"]
    rows = []
    hz_grid = (12.5, 25.0, 50.0) if cfg["name"] != "smoke" else (25.0,)
    sec_grid = (0.5, 1.0, 2.0, 5.0) if cfg["name"] != "smoke" else (1.0, 4.0)
    n_subj = min(cfg["n_subjects"], 8)
    n_win = min(cfg["windows_per_class"], 4)
    for hz in hz_grid:
        for sec in sec_grid:
            b = make_cohort_bundle(
                n_subjects=n_subj,
                windows_per_class=n_win,
                seed=cfg["seed"],
                hz=hz,
                seconds=sec,
                noise_std=cfg["noise_std"],
                label_noise=cfg["label_noise"],
            )
            oof, _, folds, _ = group_cv_oof(
                "logreg", proto, b.X, b.y_gait, b.subject_id, b.feature_names, min(cfg["n_splits"], 3), cfg["seed"]
            )
            f1 = float(f1_score(b.y_gait, oof, average="macro", zero_division=0))
            rows.append(
                {
                    "sample_hz": hz,
                    "window_seconds": sec,
                    "n_samples": int(b.windows.shape[1]),
                    "macro_f1": f1,
                    "fold_macro_f1_mean": float(np.mean([r["macro_f1"] for r in folds])),
                    "data_source": "synthetic",
                    "validation_type": "engineering_simulation",
                    "note": "model trained and tested at the same fs/window; not a deployment downsample mismatch",
                }
            )
    return rows


def run_threshold_sweep(bundle: CohortBundle) -> list[dict]:
    """Binary overload vs normal using engineering peak thresholds."""
    y_bin = (bundle.y_gait != "normal").astype(int)
    peak = bundle.X[:, bundle.feature_names.index("peak_any")]
    rows = []
    for thr in (40, 55, 75, 100, 125, 150, 200):
        pred = (peak >= thr).astype(int)
        tp = int(((pred == 1) & (y_bin == 1)).sum())
        tn = int(((pred == 0) & (y_bin == 0)).sum())
        fp = int(((pred == 1) & (y_bin == 0)).sum())
        fn = int(((pred == 0) & (y_bin == 1)).sum())
        sens = tp / (tp + fn) if tp + fn else 0.0
        spec = tn / (tn + fp) if tn + fp else 0.0
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = sens
        f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) else 0.0
        rows.append(
            {
                "threshold_kpa": thr,
                "sensitivity": sens,
                "specificity": spec,
                "precision": prec,
                "recall": rec,
                "f1": f1,
                "false_alert_rate": fp / max(fp + tn, 1),
                "missed_event_rate": fn / max(fn + tp, 1),
                "n_positive_true": int(y_bin.sum()),
                "label_definition": "synthetic gait class != normal (not a clinical ulcer event)",
                "threshold_type": "engineering_risk_alert",
                "data_source": bundle.data_source,
            }
        )
    return rows


def run_latency(bundle: CohortBundle, fitted: dict, cfg: dict) -> list[dict]:
    rows = []
    # packet codec
    pkt_times = []
    raw = encode_packet("left", 1, 1000, (400, 500, 300, 600), 90)
    for _ in range(200):
        t0 = time.perf_counter()
        decode_packet(raw)
        pkt_times.append((time.perf_counter() - t0) * 1000.0)
    arr = np.asarray(pkt_times)
    rows.append(
        {
            "Stage": "BLE packet decode (host, not radio)",
            "Mean Latency": float(arr.mean()),
            "Median": float(np.median(arr)),
            "P95": float(np.percentile(arr, 95)),
            "P99": float(np.percentile(arr, 99)),
            "Std Dev": float(arr.std(ddof=1)),
            "Notes": "Software decode of 28-byte payload. Radio/airtime not measured in this repo.",
        }
    )
    feat_times = []
    w = bundle.windows[0]
    for _ in range(max(cfg["latency_repeats"], 10)):
        t0 = time.perf_counter()
        extract_features(GaitWindow(w, sample_hz=bundle.sample_hz))
        feat_times.append((time.perf_counter() - t0) * 1000.0)
    arr = np.asarray(feat_times)
    rows.append(
        {
            "Stage": "Preprocessing / feature extraction",
            "Mean Latency": float(arr.mean()),
            "Median": float(np.median(arr)),
            "P95": float(np.percentile(arr, 95)),
            "P99": float(np.percentile(arr, 99)),
            "Std Dev": float(arr.std(ddof=1)),
            "Notes": f"{bundle.window_seconds}s window at {bundle.sample_hz} Hz, host CPU.",
        }
    )
    for name, est in fitted.items():
        eff = model_efficiency_row(name, est, bundle.X[:32])
        rows.append(
            {
                "Stage": f"Inference ({name})",
                "Mean Latency": eff["mean_ms"],
                "Median": eff["median_ms"],
                "P95": eff["p95_ms"],
                "P99": eff.get("p99_ms", ""),
                "Std Dev": eff["std_ms"],
                "Notes": f"serialized {eff['serialized_kb']} KB; params={eff['n_params']}",
            }
        )
    # design-spec rows (not measured)
    rows.append(
        {
            "Stage": "FSR sample period (firmware design)",
            "Mean Latency": 40.0,
            "Median": 40.0,
            "P95": 40.0,
            "Std Dev": "",
            "Notes": "25 Hz design specification from firmware delay; not a scope measurement.",
        }
    )
    rows.append(
        {
            "Stage": "BLE radio notify (not measured)",
            "Mean Latency": "",
            "Median": "",
            "P95": "",
            "Std Dev": "",
            "Notes": "Requires instrumented ESP32 + phone capture. Do not invent values.",
        }
    )
    inf_logreg = next((r for r in rows if r["Stage"] == "Inference (logreg)"), None)
    prep = next(r for r in rows if r["Stage"].startswith("Preprocessing"))
    if inf_logreg and inf_logreg.get("Mean Latency") not in ("", None):
        rows.append(
            {
                "Stage": "Host alert path (features + logreg)",
                "Mean Latency": float(prep["Mean Latency"]) + float(inf_logreg["Mean Latency"]),
                "Median": "",
                "P95": float(prep["P95"]) + float(inf_logreg["P95"]),
                "P99": "",
                "Std Dev": "",
                "Notes": "Excludes BLE airtime and UI render. Uses logistic regression only (not RF mean).",
            }
        )
    return rows


def run_calibration_demo() -> dict:
    CAL.mkdir(parents=True, exist_ok=True)
    write_template_csv(CAL / "TEMPLATE.csv")
    cal = SensorCalibration(site="met1", model="loglog", version="simulated_example_v0")
    sim = simulate_example_curve(cal, seed=67)
    resid = calibration_residuals(sim["force_true_n"], sim["force_pred_n"])
    plot_calibration_figures(sim, resid, FIG, caption_note="SIMULATED example — not a physical bench measurement")
    _json(
        RES / "calibration_simulated.json",
        {
            "data_source": "simulated_example",
            "validation_type": "pipeline_demo",
            "residuals": resid,
            "note": "Generated from a known log-log curve plus ADC noise. Not this device's bench calibration.",
        },
    )
    header = "site,trial,direction,force_n,adc,notes\n"
    lines = [header]
    for i, (f, a, d) in enumerate(zip(sim["force_true_n"], sim["adc"], sim["direction"])):
        lines.append(f"met1,sim,{d},{f:.4f},{a:.2f},SIMULATED\n")
    (CAL / "SIMULATED_example.csv").write_text("".join(lines))
    return resid


def fit_production(bundle: CohortBundle) -> dict:
    tr, te = grouped_train_test_split(
        bundle.X, bundle.y_gait, bundle.subject_id, test_size=0.2, random_state=67, kind="subject"
    )
    gait = gait_pipeline()
    gait.fit(bundle.X[tr], bundle.y_gait[tr])
    zone = zone_pipeline()
    zone.fit(bundle.X[tr], bundle.y_zone[tr])
    save_artifact(gait, "gait_pattern_rf.joblib")
    save_artifact(zone, "high_risk_zone_gbm.joblib")
    fitted = {"logreg_production": gait, "zone_gbm": zone}
    for name, proto in baseline_models().items():
        if name not in ("logreg", "decision_tree", "random_forest", "linear_svm", "threshold_heuristic"):
            continue
        m = _prepare_model(name, proto, bundle.feature_names)
        m.fit(bundle.X[tr], bundle.y_gait[tr])
        fitted[name] = m
    return {"fitted": fitted, "train_idx": tr, "test_idx": te}


def ulcer_placeholder() -> dict:
    archive = _ROOT / "ulcer model" / "archive"
    present = (archive / "train").is_dir()
    return {
        "task": "dfu_photograph_grade",
        "dataset_present": present,
        "data_source": "public_roboflow_kaggle" if present else "not_in_checkout",
        "validation_type": "computer_vision_public_images" if present else "skipped",
        "note": (
            "Ulcer CNN uses public photographs, not insole pressure. "
            "Do not treat image accuracy as plantar-pressure generalization. "
            "Images are gitignored; run scripts/train_ulcer.py when the archive is local."
        ),
        "metrics": None,
    }


def hardware_table() -> list[dict]:
    return [
        {"item": "Sensors", "specification": "4 × FSR402-class force-sensitive resistors"},
        {"item": "Sites", "specification": "MET1, MET2, MET5, HEEL (canonical names)"},
        {"item": "MCU", "specification": "ESP32, 12-bit ADC, 10 kΩ divider"},
        {"item": "Wireless", "specification": "BLE Nordic UART-style UUIDs, 28-byte LE payload"},
        {"item": "Nominal rate", "specification": "25 Hz (40 ms loop; design spec)"},
        {"item": "Pressure map (engineering default)", "specification": "linear ADC→kPa, 250 kPa full scale; not bench-calibrated"},
        {"item": "Mobile", "specification": "Expo / React Native client; not the scientific novelty"},
    ]


def main() -> dict:
    cfg = _cfg()
    RES.mkdir(parents=True, exist_ok=True)
    TAB.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)

    cal = run_calibration_demo()
    bundle = make_cohort_bundle(
        n_subjects=cfg["n_subjects"],
        windows_per_class=cfg["windows_per_class"],
        seed=cfg["seed"],
        hz=cfg["hz"],
        seconds=cfg["seconds"],
        noise_std=cfg["noise_std"],
        label_noise=cfg["label_noise"],
    )
    recs = [
        PressureWindowRecord(
            subject_id=str(int(s)),
            session_id=str(sess),
            sample_hz=bundle.sample_hz,
            calibration_version=bundle.calibration_version,
            firmware_version=bundle.firmware_version,
            pressure_kpa=w.tolist(),
            packet_loss_frac=0.0,
            gait_label=str(g),
            zone_label=str(z),
            data_source="synthetic",
        )
        for s, sess, w, g, z in zip(
            bundle.subject_id[: min(8, len(bundle.subject_id))],
            bundle.session_id[: min(8, len(bundle.session_id))],
            bundle.windows[: min(8, len(bundle.windows))],
            bundle.y_gait[: min(8, len(bundle.y_gait))],
            bundle.y_zone[: min(8, len(bundle.y_zone))],
        )
    ]
    validate_records(recs)

    baselines, oof_store, extra = run_baselines(bundle, cfg)
    sensor_rows = run_sensor_ablation(bundle, cfg)
    feat_rows = run_feature_ablation(bundle, cfg)
    robust_rows = run_robustness(bundle, cfg)
    window_rows = run_window_fs(cfg)
    thr_rows = run_threshold_sweep(bundle)
    prod = fit_production(bundle)
    lat_rows = run_latency(bundle, prod["fitted"], cfg)
    eff_rows = [model_efficiency_row(n, m, bundle.X[:32]) for n, m in prod["fitted"].items()]

    mcnemar = None
    if "logreg" in oof_store and "random_forest" in oof_store:
        mcnemar = mcnemar_b(bundle.y_gait, oof_store["random_forest"], oof_store["logreg"])

    dhash = dataset_hash(bundle.X, bundle.y_gait, bundle.subject_id)
    payload = {
        "validation_type": "engineering_simulation",
        "data_source": "synthetic",
        "config": cfg,
        "n_windows": int(len(bundle.y_gait)),
        "n_subjects": int(len(np.unique(bundle.subject_id))),
        "dataset_hash": dhash,
        "calibration_simulated_residuals": cal,
        "baselines": baselines,
        "per_model": extra,
        "sensor_ablation": sensor_rows,
        "feature_ablation": feat_rows,
        "robustness": robust_rows,
        "window_fs": window_rows,
        "threshold_sweep": thr_rows,
        "latency": lat_rows,
        "efficiency": eff_rows,
        "mcnemar_rf_vs_logreg": mcnemar,
        "ulcer": ulcer_placeholder(),
        "alert_threshold_kpa": ALERT_PRESSURE_KPA,
        "alert_threshold_type": "engineering_risk_alert",
    }
    _json(RES / "research_results.json", payload)
    write_manifest(
        RES / "manifest.json",
        {
            "experiment": "ehb26_research_pipeline",
            "validation_type": "engineering_simulation",
            "data_source": "synthetic",
            "dataset_hash": dhash,
            "config": cfg,
            "n_windows": payload["n_windows"],
            "n_subjects": payload["n_subjects"],
            "environment": environment_record(),
        },
    )
    _write_csv(TAB / "table3_model_comparison.csv", baselines)
    _write_csv(TAB / "table4_sensor_ablation.csv", sensor_rows)
    _write_csv(TAB / "table5_robustness.csv", robust_rows)
    _write_csv(
        TAB / "table6_system_performance.csv",
        lat_rows,
        ["Stage", "Mean Latency", "Median", "P95", "P99", "Std Dev", "Notes"],
    )
    _write_csv(TAB / "table1_hardware.csv", hardware_table(), ["item", "specification"])
    _write_csv(
        TAB / "table2_dataset.csv",
        [
            {
                "dataset": "synthetic_4fsr_gait",
                "data_source": "synthetic",
                "n_subjects": payload["n_subjects"],
                "n_windows": payload["n_windows"],
                "sample_hz": bundle.sample_hz,
                "window_s": bundle.window_seconds,
                "classes": len(GAIT_CLASSES),
                "split": "GroupKFold by virtual subject",
                "labels": "simulator gait overload patterns; zone derived from gait class",
            }
        ],
    )
    _write_csv(
        TAB / "table7_ulcer.csv",
        [
            {
                "backbone": "not_run_in_default_pipeline",
                "data_source": payload["ulcer"]["data_source"],
                "macro_f1": "",
                "note": payload["ulcer"]["note"],
            }
        ],
    )
    _write_csv(TAB / "feature_ablation.csv", feat_rows)
    _write_csv(TAB / "window_fs.csv", window_rows)
    _write_csv(TAB / "threshold_sweep.csv", thr_rows)
    _write_csv(TAB / "efficiency.csv", eff_rows)
    _json(RES / "oof_logreg_cm.json", extra.get("logreg", extra.get(cfg["models"][0], {})))
    print(json.dumps({"n_windows": payload["n_windows"], "models": [r["model"] for r in baselines]}, indent=2))
    return payload


if __name__ == "__main__":
    main()
