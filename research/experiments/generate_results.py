#!/usr/bin/env python3
"""Write research/manuscript/generated_results.md from frozen CSVs (never hand-typed metrics)."""

from __future__ import annotations

import csv
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
TAB = _ROOT / "research" / "tables"
RES = _ROOT / "research" / "results"
OUT = _ROOT / "research" / "manuscript" / "generated_results.md"


def _rows(name: str) -> list[dict]:
    path = TAB / name
    if not path.exists():
        return []
    with path.open() as f:
        return list(csv.DictReader(f))


def _md(name: str, keep: list[str] | None = None) -> str:
    rows = _rows(name)
    if not rows:
        return f"_Missing or empty `{name}`._\n"
    header = keep or list(rows[0].keys())
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join(["---"] * len(header)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(k, ""))[:48] for k in header) + " |")
    return "\n".join(lines) + "\n"


def _f(row: dict, key: str, digits: int = 3) -> str:
    try:
        return f"{float(row[key]):.{digits}f}"
    except (KeyError, TypeError, ValueError):
        return "n/a"


def verify_text_contains(text: str, token: str) -> None:
    if token not in text:
        raise AssertionError(f"generated Results missing expected token {token!r}")


def main() -> None:
    meta = {}
    for name in ("final_eval.json", "research_results.json"):
        p = RES / name
        if p.exists():
            meta.update(json.loads(p.read_text()))
    models = _rows("model_comparison.csv") or _rows("table3_model_comparison.csv")
    ablation = _rows("sensor_ablation_publication.csv") or _rows("table4_sensor_ablation.csv")
    splits = _rows("split_protocol_comparison.csv")
    packet = _rows("packet_loss_sweep.csv")
    sampling = _rows("sampling_rate_tradeoff.csv")
    repeat = _rows("repeatability.csv")
    cal = json.loads((RES / "calibration_evaluation.json").read_text()) if (RES / "calibration_evaluation.json").exists() else {}
    lat = json.loads((RES / "latency_host.json").read_text()) if (RES / "latency_host.json").exists() else {}
    proba = json.loads((RES / "probability_calibration.json").read_text()) if (RES / "probability_calibration.json").exists() else {}

    logreg = next((r for r in models if r.get("model") == "logreg"), {})
    four = next((r for r in ablation if str(r.get("subset")) == "4_all" or "4-site" in str(r.get("Sensor Configuration", ""))), {})
    drop_met5 = next((r for r in ablation if "no_met5" in str(r.get("subset", ""))), {})
    drop_heel = next((r for r in ablation if "no_heel" in str(r.get("subset", ""))), {})
    iid = next((r for r in splits if r.get("protocol") == "iid_window"), {})
    subj = next((r for r in splits if r.get("protocol") == "subject"), {})
    sess = next((r for r in splits if r.get("protocol") == "session"), {})
    pkt30 = next((r for r in packet if str(r.get("severity")) in ("0.3", "0.30")), {})
    samp50 = next((r for r in sampling if str(r.get("keep_fraction")) in ("0.5", "0.50")), {})
    peak_cv = next((r for r in repeat if r.get("feature") == "peak_any"), {})

    ds = meta.get("data_source") or logreg.get("data_source") or "synthetic"
    n_win = meta.get("n_windows") or logreg.get("n_windows") or "?"
    n_subj = meta.get("n_subjects") or logreg.get("n_subjects") or "?"

    parts = [
        "# Results (generated from frozen tables)",
        "",
        "These numbers are copied from CSV/JSON under `research/tables` and `research/results`. ",
        "They are **not** typed by hand. **Data source for all quantitative ML rows below is "
        f"`{ds}`** unless a row says otherwise. This is **not** patient generalization.",
        "",
        f"Cohort: **{n_win}** windows, **{n_subj}** virtual subjects, 25 Hz, 4 s windows, GroupKFold by subject unless specified.",
        "",
        "## 6.1 Baseline models (subject-independent)",
        "",
        f"Logistic regression achieved macro-F1 **{_f(logreg, 'macro_f1')}** "
        f"(bootstrap 95% CI {_f(logreg, 'macro_f1_ci95_lo')}–{_f(logreg, 'macro_f1_ci95_hi')}) "
        f"on grouped out-of-fold predictions"
        + (f"; OOF AUROC {_f(logreg, 'auroc_macro')}" if logreg.get("auroc_macro") not in (None, "") else "")
        + ". A majority-class dummy and a threshold heuristic are far lower. "
        "Small decimal gaps between logreg, hist-GBM, and MLP should not be interpreted as a meaningful ranking without overlapping-CI checks.",
        "",
        _md(
            "model_comparison.csv" if (TAB / "model_comparison.csv").exists() else "table3_model_comparison.csv",
            [
                "model",
                "accuracy",
                "balanced_accuracy",
                "macro_f1",
                "macro_f1_ci95_lo",
                "macro_f1_ci95_hi",
                "auroc_macro",
                "serialized_kb",
                "inference_mean_ms",
            ]
            if (TAB / "model_comparison.csv").exists()
            else None,
        ),
        "## 6.2 Split protocol (leakage check)",
        "",
        "Random-window (IID) splitting can mix the same virtual subject across train and test. "
        f"IID macro-F1 **{_f(iid, 'macro_f1')}** vs subject-grouped **{_f(subj, 'macro_f1')}** "
        f"vs session-grouped **{_f(sess, 'macro_f1')}**. "
        "If IID is substantially higher, the gap is treated as evidence of optimistic validation, not as a better model.",
        "",
        _md("split_protocol_comparison.csv", ["protocol", "macro_f1", "accuracy", "macro_f1_ci95_lo", "macro_f1_ci95_hi", "note"]),
        "## 6.3 Four-sensor ablation",
        "",
        f"The four-site configuration macro-F1 is **{_f(four, 'Performance') or _f(four, 'macro_f1')}**. "
        f"Dropping MET5 yields **{_f(drop_met5, 'Performance') or _f(drop_met5, 'macro_f1')}**; "
        f"dropping HEEL yields **{_f(drop_heel, 'Performance') or _f(drop_heel, 'macro_f1')}**. "
        "Single-site models remain near chance-to-weak. Four sensors are a **cost/information tradeoff on this simulator**, "
        "not a proof of clinical optimality.",
        "",
        _md(
            "sensor_ablation_publication.csv" if (TAB / "sensor_ablation_publication.csv").exists() else "table4_sensor_ablation.csv",
            ["Sensor Configuration", "Performance", "delta_vs_4_sensor", "Feature Count", "Notes"]
            if (TAB / "sensor_ablation_publication.csv").exists()
            else None,
        ),
        "## 6.4 Robustness",
        "",
        f"Under simulated BLE packet loss of 30%, held-out-subject macro-F1 is **{_f(pkt30, 'macro_f1')}**. "
        "Degradation curves are reported in full; failure points are not hidden.",
        "",
        _md("packet_loss_sweep.csv"),
        "## 6.5 Sampling rate (no fake upsampling)",
        "",
        f"Training remains at 25 Hz. Testing on a 50% subsample (original samples only) yields macro-F1 **{_f(samp50, 'macro_f1')}**. "
        "BLE payload rate scales with sample rate (28 bytes × 2 feet × Hz).",
        "",
        _md("sampling_rate_tradeoff.csv", ["label", "effective_hz", "macro_f1", "ble_bytes_per_s_two_feet", "note"]),
        "## 6.6 Repeatability",
        "",
        "Human test–retest ICC is **not reported** (no repeated walking sessions in-repo). "
        f"Simulator within-session CV for `peak_any` (median) is **{_f(peak_cv, 'within_session_cv_median')}**; "
        f"between-seed ICC is **{_f(peak_cv, 'between_seed_icc')}**. These characterize the generator, not a person.",
        "",
        _md("repeatability.csv"),
        "## 6.7 Sensor calibration vs ML accuracy",
        "",
        "These quantities are not interchangeable. Simulated log–log reconstruction "
        f"(not a bench measurement): MAE **{cal.get('mae_n', 'n/a')}** N, "
        f"RMSE **{cal.get('rmse_n', 'n/a')}** N, MAPE **{cal.get('mape_pct', 'n/a')}** %. "
        "Physical load-cell residuals remain unmeasured.",
        "",
        "## 6.8 Host latency (radio not measured)",
        "",
        f"Feature extraction mean **{lat.get('feature_mean_ms', 'n/a')}** ms; logreg mean **{lat.get('logreg_mean_ms', 'n/a')}** ms; "
        f"combined host path mean **{lat.get('host_path_mean_ms', 'n/a')}** ms "
        f"(P95 **{lat.get('host_path_p95_ms', 'n/a')}**, P99 **{lat.get('host_path_p99_ms', 'n/a')}**). "
        "Firmware sample period is 40 ms by design. BLE airtime is unmeasured.",
        "",
        "## 6.9 Probability calibration",
        "",
        f"OOF ECE **{proba.get('ece_oof', 'n/a')}**, Brier **{proba.get('brier_oof', 'n/a')}**, AUROC **{proba.get('auroc_oof', 'n/a')}**. "
        "Platt scaling was fit on inner training groups only and is **not** adopted as the production calibrator "
        "(holdout Brier did not improve). Reliability diagrams use grouped OOF probabilities.",
        "",
        "## 6.10 Thresholds",
        "",
        "Peak-pressure cut-offs are **engineering risk-alert operating points** on synthetic non-normal vs normal labels, "
        "not medically validated ulcer thresholds.",
        "",
        _md("threshold_sweep.csv"),
        "## 6.11 Window duration (same-fs train/test)",
        "",
        _md("window_fs.csv", ["sample_hz", "window_seconds", "macro_f1", "note"]),
        "",
        "The frozen 4 s / 25 Hz window is a compromise between cadence estimates (need several steps) and alert latency. "
        "It is justified by this grid plus the 25 Hz firmware spec, not by clinical outcome data.",
        "",
    ]
    text = "\n".join(parts)
    if logreg.get("macro_f1"):
        verify_text_contains(text, _f(logreg, "macro_f1"))
    OUT.write_text(text)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
