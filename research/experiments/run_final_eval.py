#!/usr/bin/env python3
"""Last-mile EHB evaluation on the frozen synthetic cohort (and human data if present).

Does not fabricate human metrics. Extra tables/figures are labeled with data_source.
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
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import GroupKFold, GroupShuffleSplit, StratifiedKFold

from research.experiments.run_research import (
    _cfg,
    _features,
    _json,
    _prepare_model,
    _write_csv,
    group_cv_oof,
)
from xstep_ml.biomechanics import GaitWindow, extract_features
from xstep_ml.calibration import (
    SensorCalibration,
    calibration_residuals,
    hysteresis_error,
    simulate_example_curve,
)
from xstep_ml.data.synthetic_gait import make_cohort_bundle
from xstep_ml.evaluation.baselines import baseline_models
from xstep_ml.evaluation.perturbations import (
    SENSOR_SUBSETS,
    dropped_packets,
    gaussian_noise,
    mask_sites,
    subset_label,
)
from xstep_ml.evaluation.publication import bootstrap_macro_f1, classification_suite, expected_calibration_error
from xstep_ml.evaluation.splits import (
    assert_no_group_overlap,
    dump_split_definitions,
    grouped_train_test_split,
    leave_one_subject_out,
)
from xstep_ml.evaluation.stats import coefficient_of_variation, icc_1_1, mean_absolute_deviation
from xstep_ml.models.gait import GAIT_CLASSES

RES = _ROOT / "research" / "results"
TAB = _ROOT / "research" / "tables"
FIG = _ROOT / "research" / "figures"
SPLIT_DIR = RES / "splits"
CAPTION = "Synthetic / engineering validation — not patient data."
REPEAT_FEATURES = (
    "peak_any",
    "pti_total",
    "cadence_spm",
    "stance_ratio",
    "forefoot_share",
    "L_met1_peak",
    "L_met2_peak",
    "L_met5_peak",
    "L_heel_peak",
    "L_met2_load",
)


def _savefig(fig, stem: str, close: bool = True) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    for ext in (".png", ".pdf", ".svg"):
        fig.savefig(FIG / f"{stem}{ext}", dpi=300, bbox_inches="tight")
    if close:
        plt.close(fig)


def _read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open() as f:
        return list(csv.DictReader(f))


def _oof_on_groups(proto, name, X, y, groups, feature_names, n_splits, seed, protocol: str):
    if protocol == "iid_window":
        skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
        folds = list(skf.split(X, y))
        oof = np.empty(len(y), dtype=object)
        for tr, te in folds:
            clf = _prepare_model(name, proto, feature_names)
            clf.fit(X[tr], y[tr])
            oof[te] = clf.predict(X[te])
        dump_split_definitions(SPLIT_DIR / "iid_window.json", folds, groups, protocol="iid_window", y=y)
        return oof.astype(str)
    if protocol == "loso":
        folds = leave_one_subject_out(groups)
        dump_split_definitions(SPLIT_DIR / "loso_subject.json", folds, groups, protocol="subject", y=y)
    else:
        kind = "session" if protocol == "session" else "subject"
        n_groups = len(np.unique(groups))
        gkf = GroupKFold(n_splits=min(n_splits, n_groups))
        folds = list(gkf.split(X, y, groups))
        for tr, te in folds:
            assert_no_group_overlap(groups[tr], groups[te], kind=kind)
        dump_split_definitions(SPLIT_DIR / f"{protocol}_groupkfold.json", folds, groups, protocol=kind, y=y)
    oof = np.empty(len(y), dtype=object)
    for tr, te in folds:
        clf = _prepare_model(name, proto, feature_names)
        clf.fit(X[tr], y[tr])
        oof[te] = clf.predict(X[te])
    return oof.astype(str)


def run_split_protocols(bundle, cfg) -> list[dict]:
    proto = baseline_models(cfg["seed"])["logreg"]
    names = bundle.feature_names
    rows = []
    protocols = [
        ("iid_window", bundle.subject_id, "random windows (subject leakage possible)"),
        ("session", bundle.session_id, "GroupKFold by session_id"),
        ("subject", bundle.subject_id, "GroupKFold by subject_id"),
    ]
    n_splits = cfg["n_splits"]
    if cfg["name"] != "smoke":
        protocols.append(("loso", bundle.subject_id, "leave-one-subject-out"))
    for protocol, groups, note in protocols:
        splits = n_splits if protocol != "loso" else min(len(np.unique(groups)), 24)
        if protocol == "loso":
            oof = _oof_on_groups(proto, "logreg", bundle.X, bundle.y_gait, groups, names, splits, cfg["seed"], "loso")
        else:
            oof = _oof_on_groups(proto, "logreg", bundle.X, bundle.y_gait, groups, names, n_splits, cfg["seed"], protocol)
        suite = classification_suite(bundle.y_gait, oof, labels=list(GAIT_CLASSES))
        f1 = bootstrap_macro_f1(bundle.y_gait, oof, n_boot=cfg["n_boot"], seed=cfg["seed"])
        rows.append(
            {
                "protocol": protocol,
                "macro_f1": suite["macro_f1"],
                "accuracy": suite["accuracy"],
                "balanced_accuracy": suite["balanced_accuracy"],
                "macro_f1_ci95_lo": f1["ci95_lo"],
                "macro_f1_ci95_hi": f1["ci95_hi"],
                "n_windows": int(len(bundle.y_gait)),
                "note": note,
                "data_source": bundle.data_source,
                "validation_type": "engineering_simulation",
            }
        )
    return rows


def run_extra_ablation(bundle, cfg, existing: list[dict]) -> list[dict]:
    have = {r.get("subset") for r in existing}
    proto = baseline_models(cfg["seed"])["logreg"]
    rows = list(existing)
    extra_keys = [k for k in SENSOR_SUBSETS if k not in have]
    if "4_all" not in have:
        extra_keys = ["4_all"] + [k for k in extra_keys if k != "4_all"]
    if cfg["name"] == "smoke":
        extra_keys = [k for k in extra_keys if k in ("4_all", "3_no_heel", "1_met1")] or extra_keys[:3]
    for key in extra_keys:
        keep = SENSOR_SUBSETS[key]
        X = _features(mask_sites(bundle.windows, keep), bundle.sample_hz)
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
    four = next(float(r["macro_f1"]) for r in rows if r.get("subset") == "4_all")
    out = []
    for r in rows:
        f1 = float(r["macro_f1"])
        n_sites = int(float(r.get("n_sites") or len(SENSOR_SUBSETS.get(r.get("subset", ""), [0, 1, 2, 3]))))
        out.append(
            {
                "Sensor Configuration": r.get("label") or r.get("subset"),
                "subset": r.get("subset"),
                "Performance": f1,
                "delta_vs_4_sensor": f1 - four,
                "Feature Count": 59,
                "n_sites": n_sites,
                "macro_f1_ci95_lo": r.get("macro_f1_ci95_lo"),
                "macro_f1_ci95_hi": r.get("macro_f1_ci95_hi"),
                "Notes": "59 features still extracted; dropped sites are zeroed. Synthetic labels.",
                "data_source": r.get("data_source", "synthetic"),
            }
        )
    return out


def run_packet_and_noise(bundle, cfg) -> tuple[list[dict], list[dict]]:
    rng = np.random.default_rng(cfg["seed"] + 9)
    tr, te = grouped_train_test_split(bundle.X, bundle.y_gait, bundle.subject_id, test_size=0.25, random_state=cfg["seed"])
    clf = _prepare_model("logreg", baseline_models(cfg["seed"])["logreg"], bundle.feature_names)
    clf.fit(bundle.X[tr], bundle.y_gait[tr])
    test_w = bundle.windows[te]
    y_te = bundle.y_gait[te]
    hz = bundle.sample_hz

    def _eval(tag, severity, windows):
        pred = clf.predict(_features(windows, hz))
        return {
            "perturbation": tag,
            "severity": severity,
            "macro_f1": float(f1_score(y_te, pred, average="macro", zero_division=0)),
            "accuracy": float(accuracy_score(y_te, pred)),
            "data_source": bundle.data_source,
            "validation_type": "engineering_simulation",
        }

    packet = [_eval("dropped_packets_frac", 0.0, test_w)]
    for s in (0.01, 0.05, 0.10, 0.20, 0.30):
        packet.append(_eval("dropped_packets_frac", s, dropped_packets(test_w, rng, s)))
    noise = [_eval("gaussian_noise_kpa", 0.0, test_w)]
    for s in (1.5, 3.5, 7.0, 12.0):
        noise.append(_eval("gaussian_noise_kpa", s, gaussian_noise(test_w, rng, s)))
    return packet, noise


def downsample_original_samples(windows: np.ndarray, keep_frac: float) -> tuple[np.ndarray, float]:
    """Keep a subset of original samples. Does not interpolate new values."""
    t = windows.shape[1]
    new_t = max(2, int(round(t * keep_frac)))
    idx = np.round(np.linspace(0, t - 1, new_t)).astype(int)
    return windows[:, idx, :], new_t / t


def run_sampling_tradeoff(bundle, cfg) -> list[dict]:
    rng_note = "train at 25 Hz; test uses original samples only (no upsampling)"
    tr, te = grouped_train_test_split(bundle.X, bundle.y_gait, bundle.subject_id, test_size=0.25, random_state=cfg["seed"])
    clf = _prepare_model("logreg", baseline_models(cfg["seed"])["logreg"], bundle.feature_names)
    clf.fit(bundle.X[tr], bundle.y_gait[tr])
    y_te = bundle.y_gait[te]
    test_w = bundle.windows[te]
    rows = []
    ble_bytes_per_s_full = 28 * 2 * bundle.sample_hz
    for frac, label in ((1.0, "100% (25 Hz)"), (0.75, "75%"), (0.50, "50% (12.5 Hz)"), (0.25, "25% (6.25 Hz)")):
        w, realized = downsample_original_samples(test_w, frac)
        new_hz = bundle.sample_hz * realized
        pred = clf.predict(_features(w, new_hz))
        t0 = time.perf_counter()
        _features(w[: min(8, len(w))], new_hz)
        feat_ms = (time.perf_counter() - t0) / max(min(8, len(w)), 1) * 1000.0
        rows.append(
            {
                "keep_fraction": frac,
                "label": label,
                "effective_hz": new_hz,
                "n_samples": int(w.shape[1]),
                "macro_f1": float(f1_score(y_te, pred, average="macro", zero_division=0)),
                "accuracy": float(accuracy_score(y_te, pred)),
                "ble_bytes_per_s_two_feet": ble_bytes_per_s_full * frac,
                "feature_extract_ms_est": feat_ms,
                "note": rng_note,
                "data_source": bundle.data_source,
                "validation_type": "engineering_simulation",
            }
        )
    return rows


def run_repeatability(cfg) -> list[dict]:
    """Synthetic within-session CV and two-seed test-retest. Human rows empty if no data."""
    b1 = make_cohort_bundle(
        n_subjects=cfg["n_subjects"],
        windows_per_class=cfg["windows_per_class"],
        seed=cfg["seed"],
        hz=cfg["hz"],
        seconds=cfg["seconds"],
        noise_std=cfg["noise_std"],
        label_noise=0.0,
    )
    b2 = make_cohort_bundle(
        n_subjects=cfg["n_subjects"],
        windows_per_class=cfg["windows_per_class"],
        seed=cfg["seed"] + 1,
        hz=cfg["hz"],
        seconds=cfg["seconds"],
        noise_std=cfg["noise_std"],
        label_noise=0.0,
    )
    names = b1.feature_names
    rows = []
    for feat in REPEAT_FEATURES:
        if feat not in names:
            continue
        j = names.index(feat)
        cvs = []
        mads = []
        for sess in np.unique(b1.session_id):
            mask = b1.session_id == sess
            vals = b1.X[mask, j]
            if len(vals) < 3:
                continue
            cvs.append(coefficient_of_variation(vals))
            mads.append(mean_absolute_deviation(vals))
        # subject-level means for same gait session across two generator seeds
        means1, means2 = [], []
        for sid in np.unique(b1.subject_id):
            for sess in np.unique(b1.session_id[b1.subject_id == sid]):
                m1 = b1.session_id == sess
                m2 = b2.session_id == sess
                if m1.sum() == 0 or m2.sum() == 0:
                    continue
                means1.append(float(b1.X[m1, j].mean()))
                means2.append(float(b2.X[m2, j].mean()))
        ratings = np.column_stack([means1, means2]) if means1 else np.zeros((0, 2))
        icc = icc_1_1(ratings) if len(ratings) >= 2 else float("nan")
        rows.append(
            {
                "feature": feat,
                "within_session_cv_median": float(np.nanmedian(cvs)) if cvs else "",
                "within_session_mad_median": float(np.nanmedian(mads)) if mads else "",
                "between_seed_icc": icc,
                "n_sessions": int(len(cvs)),
                "data_source": "synthetic",
                "validation_type": "engineering_simulation",
                "note": "Simulator test-retest (seeds 67 vs 68), not human ICC",
            }
        )
    human_processed = _ROOT / "data" / "processed"
    has_human = False
    if human_processed.is_dir():
        for man in human_processed.glob("*/import_manifest.json"):
            meta = json.loads(man.read_text())
            if int(meta.get("n_sessions_imported") or 0) > 0:
                has_human = True
    if not has_human:
        rows.append(
            {
                "feature": "HUMAN_REPEATABILITY",
                "within_session_cv_median": "",
                "within_session_mad_median": "",
                "between_seed_icc": "",
                "n_sessions": 0,
                "data_source": "absent",
                "validation_type": "not_run",
                "note": "No human repeated walking sessions in data/raw; values not fabricated",
            }
        )
    return rows


def run_calibration_report() -> dict:
    cal = SensorCalibration(site="met1", model="loglog", version="simulated_example_v0")
    sim = simulate_example_curve(cal, seed=67)
    resid = calibration_residuals(sim["force_true_n"], sim["force_pred_n"])
    load = sim["force_pred_n"][sim["direction"] == "loading"]
    unload = sim["force_pred_n"][sim["direction"] == "unloading"]
    n = min(len(load), len(unload))
    hyst = hysteresis_error(load[:n][::-1], unload[:n]) if n else float("nan")
    payload = {
        "task": "sensor_calibration_not_ml_accuracy",
        "data_source": "simulated_example",
        "mae_n": resid["mae_n"],
        "rmse_n": resid["rmse_n"],
        "mape_pct": resid["mape_pct"],
        "hysteresis_mae_n": hyst,
        "ml_accuracy_note": "These residuals are sensor-curve reconstruction error on a simulated load cell, not classification macro-F1.",
        "physical_bench_present": False,
    }
    _json(RES / "calibration_evaluation.json", payload)
    return payload


def run_logreg_proba(bundle, cfg) -> dict:
    proto = baseline_models(cfg["seed"])["logreg"]
    oof, proba, folds, labels = group_cv_oof(
        "logreg", proto, bundle.X, bundle.y_gait, bundle.subject_id, bundle.feature_names, cfg["n_splits"], cfg["seed"]
    )
    suite = classification_suite(bundle.y_gait, oof, proba, labels=labels)
    dump_split_definitions(
        SPLIT_DIR / "subject_groupkfold.json",
        list(GroupKFold(n_splits=min(cfg["n_splits"], len(np.unique(bundle.subject_id)))).split(bundle.X, bundle.y_gait, bundle.subject_id)),
        bundle.subject_id,
        protocol="subject",
        y=bundle.y_gait,
    )
    pred_path = RES / "oof_logreg_predictions.csv"
    with pred_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["index", "subject_id", "session_id", "y_true", "y_pred", "correct", "peak_any"])
        peak_i = bundle.feature_names.index("peak_any")
        for i in range(len(oof)):
            w.writerow(
                [
                    i,
                    int(bundle.subject_id[i]),
                    bundle.session_id[i],
                    bundle.y_gait[i],
                    oof[i],
                    int(oof[i] == bundle.y_gait[i]),
                    float(bundle.X[i, peak_i]),
                ]
            )
    ece = suite.get("calibration") or {}
    if proba is not None:
        lab_to_i = {str(lab): i for i, lab in enumerate(labels)}
        y_int = np.array([lab_to_i[str(v)] for v in bundle.y_gait], dtype=int)
        ece = expected_calibration_error(y_int, proba)
        fig, ax = plt.subplots(figsize=(5.2, 4.2))
        ax.plot([0, 1], [0, 1], "k--", lw=1)
        bc = ece.get("bin_confidence") or []
        ba = ece.get("bin_accuracy") or []
        ax.plot(bc, ba, "o-")
        ax.set_xlabel("Confidence")
        ax.set_ylabel("Accuracy")
        ax.set_title(f"Reliability diagram (logreg OOF)\n{CAPTION}")
        _savefig(fig, "fig_reliability_logreg")
        fig, ax = plt.subplots(figsize=(5.2, 3.6))
        ax.hist(proba.max(axis=1), bins=20, color="#1f4e79")
        ax.set_xlabel("Max class probability")
        ax.set_title(f"Confidence distribution\n{CAPTION}")
        _savefig(fig, "fig_confidence_hist")
    # Platt scaling on inner groups (never test subjects)
    gss = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=cfg["seed"])
    tr, te = next(gss.split(bundle.X, bundle.y_gait, bundle.subject_id))
    inner = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=cfg["seed"] + 3)
    fit_i, cal_i = next(inner.split(bundle.X[tr], bundle.y_gait[tr], bundle.subject_id[tr]))
    base = _prepare_model("logreg", proto, bundle.feature_names)
    base.fit(bundle.X[tr][fit_i], bundle.y_gait[tr][fit_i])
    calibrated = CalibratedClassifierCV(base, method="sigmoid", cv="prefit")
    calibrated.fit(bundle.X[tr][cal_i], bundle.y_gait[tr][cal_i])
    pred_raw = base.predict(bundle.X[te])
    pred_cal = calibrated.predict(bundle.X[te])
    proba_cal = calibrated.predict_proba(bundle.X[te])
    y_te = bundle.y_gait[te]
    suite_raw = classification_suite(y_te, pred_raw, None, labels=list(GAIT_CLASSES))
    suite_cal = classification_suite(y_te, pred_cal, proba_cal, labels=list(GAIT_CLASSES))
    _json(
        RES / "probability_calibration.json",
        {
            "data_source": bundle.data_source,
            "ece_oof": ece.get("ece") if isinstance(ece, dict) else None,
            "brier_oof": suite.get("brier"),
            "auroc_oof": suite.get("auroc_macro"),
            "pr_auc_oof": suite.get("pr_auc_macro"),
            "holdout_macro_f1_raw": suite_raw["macro_f1"],
            "holdout_macro_f1_platt": suite_cal["macro_f1"],
            "holdout_brier_platt": suite_cal.get("brier"),
            "note": "Platt fitted on inner training groups only. OOF ECE uses grouped CV probabilities.",
        },
    )
    return {"oof": oof, "proba": proba, "suite": suite, "ece": ece, "folds": folds}


def run_sensor_importance(bundle, cfg) -> list[dict]:
    tr, te = grouped_train_test_split(bundle.X, bundle.y_gait, bundle.subject_id, test_size=0.25, random_state=cfg["seed"])
    clf = _prepare_model("logreg", baseline_models(cfg["seed"])["logreg"], bundle.feature_names)
    clf.fit(bundle.X[tr], bundle.y_gait[tr])
    lr = clf.named_steps["clf"]
    coef = np.abs(lr.coef_).mean(axis=0)
    site_scores = {"met1": 0.0, "met2": 0.0, "met5": 0.0, "heel": 0.0, "other": 0.0}
    for name, w in zip(bundle.feature_names, coef):
        hit = False
        for site in ("met1", "met2", "met5", "heel"):
            if site in name:
                site_scores[site] += float(w)
                hit = True
                break
        if not hit:
            site_scores["other"] += float(w)
    rows = [{"site": k, "mean_abs_logreg_coef": v, "data_source": bundle.data_source} for k, v in site_scores.items()]
    return rows


def run_error_analysis(bundle, oof) -> dict:
    y = bundle.y_gait
    wrong = oof != y
    by_class = []
    for lab in GAIT_CLASSES:
        m = y == lab
        by_class.append({"class": lab, "n": int(m.sum()), "error_rate": float(wrong[m].mean()) if m.any() else ""})
    peak_i = bundle.feature_names.index("peak_any")
    peaks = bundle.X[:, peak_i]
    tert = np.quantile(peaks, [1 / 3, 2 / 3])
    bins = np.digitize(peaks, tert)
    by_peak = []
    for b, label in enumerate(("low_peak", "mid_peak", "high_peak")):
        m = bins == b
        by_peak.append({"bin": label, "n": int(m.sum()), "error_rate": float(wrong[m].mean()) if m.any() else ""})
    by_subject = []
    for sid in np.unique(bundle.subject_id):
        m = bundle.subject_id == sid
        by_subject.append({"subject_id": int(sid), "n": int(m.sum()), "error_rate": float(wrong[m].mean())})
    rng = np.random.default_rng(67)
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.6), sharey=True)
    for ax, mask, title in (
        (axes[0], ~wrong, "Correct OOF examples"),
        (axes[1], wrong, "Incorrect OOF examples"),
    ):
        idx = np.where(mask)[0]
        if len(idx) == 0:
            continue
        pick = rng.choice(idx, size=min(3, len(idx)), replace=False)
        t = np.arange(bundle.windows.shape[1]) / bundle.sample_hz
        for i in pick:
            ax.plot(t, bundle.windows[i, :, 1], alpha=0.85, label=str(y[i])[:18])
        ax.set_title(f"{title}\n{CAPTION}")
        ax.set_xlabel("Time (s)")
        ax.legend(fontsize=6)
    axes[0].set_ylabel("L MET2 kPa")
    _savefig(fig, "fig_error_examples")
    payload = {
        "data_source": bundle.data_source,
        "n_errors": int(wrong.sum()),
        "n": int(len(y)),
        "by_class": by_class,
        "by_peak_tertile": by_peak,
        "by_subject_error_rate_mean": float(np.mean([r["error_rate"] for r in by_subject])),
        "by_subject_error_rate_std": float(np.std([r["error_rate"] for r in by_subject])),
        "worst_subjects": sorted(by_subject, key=lambda r: r["error_rate"], reverse=True)[:5],
    }
    _json(RES / "error_analysis.json", payload)
    return payload


def write_error_markdown(payload: dict) -> None:
    lines = [
        "# Error analysis",
        "",
        f"**Data source:** `{payload['data_source']}` (not patient data unless labeled human).",
        "",
        f"Out-of-fold logistic regression misclassified **{payload['n_errors']} / {payload['n']}** windows.",
        "",
        "## By class",
        "",
        "| Class | N | Error rate |",
        "| --- | --- | --- |",
    ]
    for r in payload["by_class"]:
        lines.append(f"| {r['class']} | {r['n']} | {r['error_rate']} |")
    lines += [
        "",
        "## By peak-pressure tertile",
        "",
        "Systematic weakness: if error rises in a tertile, the model is sensitive to amplitude rather than pattern.",
        "",
        "| Bin | N | Error rate |",
        "| --- | --- | --- |",
    ]
    for r in payload["by_peak_tertile"]:
        lines.append(f"| {r['bin']} | {r['n']} | {r['error_rate']} |")
    lines += [
        "",
        f"Participant-level error-rate mean (virtual subjects): {payload['by_subject_error_rate_mean']:.3f} "
        f"(SD {payload['by_subject_error_rate_std']:.3f}).",
        "",
        "Representative traces: `research/figures/fig_error_examples.*`.",
        "",
        "Human walking speed / missing-packet / footwear slices are **not available** until `data_source=human`.",
    ]
    (_ROOT / "research" / "ERROR_ANALYSIS.md").write_text("\n".join(lines) + "\n")


def merge_model_comparison(src_tab: Path | None = None) -> list[dict]:
    src_tab = src_tab or TAB
    models = _read_csv(src_tab / "table3_model_comparison.csv")
    eff = {r["model"]: r for r in _read_csv(src_tab / "efficiency.csv")}
    alias = {"logreg_production": "logreg"}
    out = []
    for r in models:
        name = r["model"]
        e = eff.get(name) or eff.get({v: k for k, v in alias.items()}.get(name, ""), {})
        if name == "logreg":
            e = eff.get("logreg") or eff.get("logreg_production") or e
        out.append(
            {
                **r,
                "n_params": e.get("n_params", ""),
                "serialized_kb": e.get("serialized_kb", ""),
                "inference_mean_ms": e.get("mean_ms", ""),
                "inference_p95_ms": e.get("p95_ms", ""),
                "inference_p99_ms": e.get("p99_ms", ""),
            }
        )
    return out


def plot_from_rows(packet, noise, sampling, ablation, splits, repeat_rows) -> None:
    sns.set_theme(style="whitegrid")
    if noise:
        fig, ax = plt.subplots(figsize=(6.4, 3.8))
        ax.plot([r["severity"] for r in noise], [r["macro_f1"] for r in noise], marker="o")
        ax.set_xlabel("Gaussian noise SD (kPa)")
        ax.set_ylabel("Macro-F1")
        ax.set_title(f"Noise robustness\n{CAPTION}")
        _savefig(fig, "fig09_robustness_noise")
    if packet:
        fig, ax = plt.subplots(figsize=(6.4, 3.8))
        ax.plot([100 * float(r["severity"]) for r in packet], [r["macro_f1"] for r in packet], marker="o")
        ax.set_xlabel("Packet loss (%)")
        ax.set_ylabel("Macro-F1")
        ax.set_title(f"Packet-loss robustness\n{CAPTION}")
        _savefig(fig, "fig10_packet_loss", close=False)
        _savefig(fig, "fig09b_packet_loss")
    if sampling:
        fig, ax = plt.subplots(figsize=(6.4, 3.8))
        ax.plot([r["effective_hz"] for r in sampling], [r["macro_f1"] for r in sampling], marker="o")
        ax.set_xlabel("Effective sampling rate (Hz)")
        ax.set_ylabel("Macro-F1")
        ax.set_title(f"Sampling-rate tradeoff (train 25 Hz)\n{CAPTION}")
        _savefig(fig, "fig13_sampling_rate")
    if ablation:
        fig, ax = plt.subplots(figsize=(8.0, 4.4))
        labels = [r["Sensor Configuration"] for r in ablation]
        vals = [float(r["Performance"]) for r in ablation]
        ax.bar(range(len(labels)), vals)
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=35, ha="right", fontsize=8)
        ax.set_ylabel("Macro-F1")
        ax.set_title(f"Sensor ablation\n{CAPTION}")
        _savefig(fig, "fig08_sensor_ablation")
    if splits:
        fig, ax = plt.subplots(figsize=(6.6, 3.8))
        ax.bar([r["protocol"] for r in splits], [float(r["macro_f1"]) for r in splits])
        ax.set_ylim(0, 1.05)
        ax.set_ylabel("Macro-F1")
        ax.set_title(f"Split protocol comparison\n{CAPTION}")
        _savefig(fig, "fig_split_protocols")
    human = [r for r in repeat_rows if r.get("feature") != "HUMAN_REPEATABILITY" and r.get("within_session_cv_median") != ""]
    if human:
        fig, ax = plt.subplots(figsize=(7.2, 3.8))
        ax.bar([r["feature"] for r in human], [float(r["within_session_cv_median"]) for r in human])
        plt.xticks(rotation=30, ha="right")
        ax.set_ylabel("Median within-session CV")
        ax.set_title(f"Repeatability (synthetic generator)\n{CAPTION}")
        _savefig(fig, "repeatability_within_session", close=False)
        _savefig(fig, "fig12_repeatability")


def latency_p99_logreg(bundle, cfg) -> dict:
    proto = _prepare_model("logreg", baseline_models(cfg["seed"])["logreg"], bundle.feature_names)
    proto.fit(bundle.X[: max(len(bundle.X) // 5, 10)], bundle.y_gait[: max(len(bundle.X) // 5, 10)])
    n = 200 if cfg["name"] != "smoke" else 20
    times = []
    row = bundle.X[:1]
    for _ in range(5):
        proto.predict(row)
    for _ in range(n):
        t0 = time.perf_counter()
        proto.predict(row)
        times.append((time.perf_counter() - t0) * 1000.0)
    arr = np.asarray(times)
    feat = []
    w = bundle.windows[0]
    for _ in range(n):
        t0 = time.perf_counter()
        extract_features(GaitWindow(w, sample_hz=bundle.sample_hz))
        feat.append((time.perf_counter() - t0) * 1000.0)
    farr = np.asarray(feat)
    host = farr + arr
    payload = {
        "feature_mean_ms": float(farr.mean()),
        "feature_p95_ms": float(np.percentile(farr, 95)),
        "feature_p99_ms": float(np.percentile(farr, 99)),
        "logreg_mean_ms": float(arr.mean()),
        "logreg_p95_ms": float(np.percentile(arr, 95)),
        "logreg_p99_ms": float(np.percentile(arr, 99)),
        "host_path_mean_ms": float(host.mean()),
        "host_path_p95_ms": float(np.percentile(host, 95)),
        "host_path_p99_ms": float(np.percentile(host, 99)),
        "n": n,
        "ble_radio_ms": None,
        "note": "Host CPU only. FSR sample period is 40 ms by firmware spec. BLE airtime not measured.",
    }
    _json(RES / "latency_host.json", payload)
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    stages = ["Feature extract", "Logreg infer", "Host path"]
    ax.barh(stages, [payload["feature_mean_ms"], payload["logreg_mean_ms"], payload["host_path_mean_ms"]])
    ax.set_xlabel("Mean latency (ms)")
    ax.set_title(f"Host latency breakdown\n{CAPTION}")
    _savefig(fig, "fig11_latency")
    return payload


def main() -> dict:
    global RES, TAB, FIG, SPLIT_DIR
    cfg = _cfg()
    if cfg["name"] != "smoke":
        cfg["n_boot"] = int(os.environ.get("BOOTSTRAP_N", "400"))
    pub_tab = _ROOT / "research" / "tables"
    if cfg["name"] == "smoke":
        base = _ROOT / "research" / "results" / "smoke"
        RES, TAB, FIG, SPLIT_DIR = base, base / "tables", base / "figures", base / "splits"
    RES.mkdir(parents=True, exist_ok=True)
    TAB.mkdir(parents=True, exist_ok=True)
    SPLIT_DIR.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)

    bundle = make_cohort_bundle(
        n_subjects=cfg["n_subjects"],
        windows_per_class=cfg["windows_per_class"],
        seed=cfg["seed"],
        hz=cfg["hz"],
        seconds=cfg["seconds"],
        noise_std=cfg["noise_std"],
        label_noise=cfg["label_noise"],
    )
    existing_ab = _read_csv(pub_tab / "table4_sensor_ablation.csv")
    ablation = run_extra_ablation(bundle, cfg, existing_ab)
    splits = run_split_protocols(bundle, cfg)
    packet, noise = run_packet_and_noise(bundle, cfg)
    sampling = run_sampling_tradeoff(bundle, cfg)
    repeat_rows = run_repeatability(cfg)
    cal = run_calibration_report()
    proba_pack = run_logreg_proba(bundle, cfg)
    importance = run_sensor_importance(bundle, cfg)
    err = run_error_analysis(bundle, proba_pack["oof"])
    if cfg["name"] != "smoke":
        write_error_markdown(err)
    models = merge_model_comparison(pub_tab)
    # fill AUROC from this OOF run into logreg row if empty
    for r in models:
        if r.get("model") == "logreg":
            r["auroc_macro"] = proba_pack["suite"].get("auroc_macro")
            r["pr_auc_macro"] = proba_pack["suite"].get("pr_auc_macro")
            r["brier"] = proba_pack["suite"].get("brier")
            ece = proba_pack.get("ece") or {}
            r["ece"] = ece.get("ece") if isinstance(ece, dict) else ""
    lat = latency_p99_logreg(bundle, cfg)
    _write_csv(TAB / "sensor_ablation_publication.csv", ablation)
    _write_csv(TAB / "model_comparison.csv", models)
    _write_csv(TAB / "split_protocol_comparison.csv", splits)
    _write_csv(TAB / "packet_loss_sweep.csv", packet)
    _write_csv(TAB / "sampling_rate_tradeoff.csv", sampling)
    _write_csv(TAB / "repeatability.csv", repeat_rows)
    _write_csv(TAB / "sensor_importance.csv", importance)
    plot_from_rows(packet, noise, sampling, ablation, splits, repeat_rows)
    summary = {
        "data_source": bundle.data_source,
        "n_windows": int(len(bundle.y_gait)),
        "n_subjects": int(len(np.unique(bundle.subject_id))),
        "split_protocols": splits,
        "calibration": cal,
        "latency_host": lat,
        "logreg_oof_macro_f1": proba_pack["suite"]["macro_f1"],
        "logreg_oof_auroc": proba_pack["suite"].get("auroc_macro"),
    }
    _json(RES / "final_eval.json", summary)
    print(json.dumps({"n_windows": summary["n_windows"], "logreg_macro_f1": summary["logreg_oof_macro_f1"]}, indent=2))
    return summary


if __name__ == "__main__":
    main()
