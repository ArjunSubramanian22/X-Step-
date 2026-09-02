#!/usr/bin/env python3
"""Write generated Results prose and rounded publication tables from the registry.

Does not retrain. Canonical numbers live in research/results/final_results_registry.json.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
TAB = _ROOT / "research" / "tables"
RES = _ROOT / "research" / "results"
REG = RES / "final_results_registry.json"
OUT = _ROOT / "research" / "manuscript" / "generated_results.md"
PUB = TAB / "publication"
SNIP = _ROOT / "research" / "manuscript" / "abstract_numbers.md"


def _rows(name: str) -> list[dict]:
    path = TAB / name
    if not path.exists():
        return []
    with path.open() as f:
        return list(csv.DictReader(f))


def _round_rows(rows: list[dict], float_keys: list[str], nd: int = 3) -> list[dict]:
    out = []
    for row in rows:
        copy = dict(row)
        for k in float_keys:
            if copy.get(k) in (None, ""):
                continue
            try:
                copy[k] = f"{float(copy[k]):.{nd}f}"
            except (TypeError, ValueError):
                pass
        out.append(copy)
    return out


def _write_csv(name: str, rows: list[dict], fields: list[str] | None = None) -> None:
    if not rows:
        return
    PUB.mkdir(parents=True, exist_ok=True)
    fields = fields or list(rows[0].keys())
    with (PUB / name).open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def _md(rows: list[dict], keep: list[str] | None = None) -> str:
    if not rows:
        return "_Missing table._\n"
    header = keep or list(rows[0].keys())
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join(["---"] * len(header)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(k, ""))[:56] for k in header) + " |")
    return "\n".join(lines) + "\n"


def _g(reg: dict, key: str) -> dict:
    return (reg.get("by_key") or {}).get(key) or {}


def _d(reg: dict, key: str, fallback: str = "n/a") -> str:
    rec = _g(reg, key)
    return str(rec.get("display") or rec.get("value") or fallback)


def verify_text_contains(text: str, token: str) -> None:
    if token not in text:
        raise AssertionError(f"generated Results missing expected token {token!r}")


def main() -> None:
    if not REG.exists():
        raise SystemExit("Run research/experiments/build_registry.py first")
    reg = json.loads(REG.read_text())
    models = _round_rows(
        _rows("model_comparison.csv"),
        [
            "accuracy",
            "balanced_accuracy",
            "precision_macro",
            "recall_macro",
            "specificity_macro",
            "macro_f1",
            "weighted_f1",
            "macro_f1_ci95_lo",
            "macro_f1_ci95_hi",
            "auroc_macro",
            "pr_auc_macro",
            "brier",
            "ece",
            "serialized_kb",
            "inference_mean_ms",
            "inference_p95_ms",
        ],
    )
    ablation = _round_rows(
        _rows("sensor_ablation_publication.csv"),
        ["Performance", "delta_vs_4_sensor", "macro_f1_ci95_lo", "macro_f1_ci95_hi"],
    )
    splits = _round_rows(
        _rows("split_protocol_comparison.csv"),
        ["macro_f1", "accuracy", "balanced_accuracy", "macro_f1_ci95_lo", "macro_f1_ci95_hi"],
    )
    packet = _round_rows(_rows("packet_loss_sweep.csv"), ["severity", "macro_f1", "accuracy"])
    sampling = _round_rows(
        _rows("sampling_rate_tradeoff.csv"),
        ["keep_fraction", "effective_hz", "macro_f1", "accuracy", "ble_bytes_per_s_two_feet"],
    )
    robust_pub = _rows("publication/table_V_robustness_summary.csv") if (PUB / "table_V_robustness_summary.csv").exists() else []
    deploy = [
        {
            "quantity": "Serialized logistic regression",
            "value": _d(reg, "logreg_serialized_kb"),
            "source": "model_comparison.csv",
        },
        {
            "quantity": "Feature extraction mean",
            "value": f"{float(_g(reg, 'host_path_mean_ms').get('value') or 0):.2f} ms path; see latency_host.json",
            "source": "latency_host.json",
        },
        {
            "quantity": "Host path mean (features + logreg)",
            "value": _d(reg, "host_path_mean_ms"),
            "source": "latency_host.json",
        },
        {
            "quantity": "Host path P95",
            "value": _d(reg, "host_path_p95_ms"),
            "source": "latency_host.json",
        },
        {
            "quantity": "Firmware sample period",
            "value": _d(reg, "firmware_sample_period_ms"),
            "source": "firmware SAMPLE_HZ=25",
        },
        {
            "quantity": "BLE radio airtime",
            "value": "not measured",
            "source": "n/a",
        },
        {
            "quantity": "Battery life",
            "value": "not measured (future work)",
            "source": "POWER_MEASUREMENT_PROTOCOL.md",
        },
    ]

    keep_models = [
        "model",
        "macro_f1",
        "macro_f1_ci95_lo",
        "macro_f1_ci95_hi",
        "accuracy",
        "auroc_macro",
        "ece",
        "serialized_kb",
        "inference_mean_ms",
        "data_source",
    ]
    keep_ab = ["Sensor Configuration", "Performance", "delta_vs_4_sensor", "n_sites", "macro_f1_ci95_lo", "macro_f1_ci95_hi", "Notes"]
    _write_csv("table_III_model_comparison.csv", models, keep_models)
    _write_csv("table_IV_sensor_ablation.csv", ablation, keep_ab)
    _write_csv(
        "table_II_dataset.csv",
        [
            {
                "dataset": "synthetic_4fsr_gait",
                "data_source": "synthetic",
                "n_subjects": _d(reg, "n_subjects_virtual"),
                "n_human_subjects": _d(reg, "n_subjects_human"),
                "n_windows": _d(reg, "n_windows"),
                "sample_hz": "25",
                "window_s": "4",
                "classes": "9 gait patterns",
                "split": "GroupKFold by virtual subject",
            },
            {
                "dataset": "human_32site_insole_optitrack",
                "data_source": "human",
                "n_subjects": _d(reg, "n_subjects_human_32site"),
                "n_human_subjects": _d(reg, "n_subjects_human_32site"),
                "n_windows": _d(reg, "n_takes_human_32site"),
                "sample_hz": "64 (assumed; no timestamps)",
                "window_s": "take (~4.6 s median)",
                "classes": "unlabeled M1–M10 takes",
                "split": "not used for frozen gait ML",
            },
        ],
    )
    _write_csv("table_VI_deployment.csv", deploy, ["quantity", "value", "source"])

    logreg_disp = _d(reg, "logreg_grouped_macro_f1")
    parts = [
        "# Results (generated from final_results_registry.json)",
        "",
        "All quantitative ML rows below are **synthetic / engineering validation** unless a cell says otherwise. ",
        "Display rounding: rates to 3 decimals; latency to 0.01 ms; force to 0.01 N. ",
        f"Registry git SHA at build: `{reg.get('git_sha', 'unknown')}`. Dataset hash: `{reg.get('dataset_hash', '')}`.",
        "",
        f"Cohort: **{_d(reg, 'n_windows')}** windows, **{_d(reg, 'n_subjects_virtual')}** virtual subjects, "
        f"**{_d(reg, 'n_subjects_human')}** X-Step four-site FSR walking subjects, "
        f"**{_d(reg, 'n_subjects_human_32site')}** adults in the 32-cell insole+OptiTrack archive "
        "(not the X-Step prototype), 25 Hz synthetic windows.",
        "",
        "## 6.1 Baseline models (subject-independent)",
        "",
        f"Logistic regression achieved macro-F1 **{logreg_disp}** on grouped out-of-fold predictions "
        f"(OOF AUROC {_d(reg, 'logreg_grouped_auroc')}; ECE {_d(reg, 'logreg_grouped_ece')}). "
        f"A majority dummy was {_d(reg, 'majority_macro_f1')} and a threshold heuristic was {_d(reg, 'heuristic_macro_f1')}. "
        f"Histogram gradient boosting was {_d(reg, 'hist_gbm_grouped_macro_f1')}; overlapping CIs mean this is not a ranking.",
        "",
        _md(models, keep_models),
        "## 6.2 Split protocol (leakage check)",
        "",
        f"IID-window macro-F1 **{_d(reg, 'iid_macro_f1')}** vs subject-grouped **{_d(reg, 'logreg_grouped_macro_f1', '0.885')}** "
        f"vs session-grouped **{_d(reg, 'session_macro_f1')}** "
        f"(Δ IID−subject = {_d(reg, 'delta_iid_minus_subject_f1')}). "
        "IID is an optimistic control, not the paper result.",
        "",
        _md(splits, ["protocol", "macro_f1", "accuracy", "macro_f1_ci95_lo", "macro_f1_ci95_hi", "note"]),
        "## 6.3 Four-sensor ablation",
        "",
        f"Within the evaluated configurations, four-site macro-F1 is **{_d(reg, 'ablation_4site_macro_f1')}**. "
        f"Dropping MET5 yields **{_d(reg, 'ablation_drop_met5_macro_f1')}** (Δ {_d(reg, 'delta_drop_met5_f1')}); "
        f"dropping HEEL yields **{_d(reg, 'ablation_drop_heel_macro_f1')}** (Δ {_d(reg, 'delta_drop_heel_f1')}); "
        f"dropping MET1 yields **{_d(reg, 'ablation_drop_met1_macro_f1')}**. "
        f"One-site MET2 is **{_d(reg, 'ablation_1site_met2_macro_f1')}**. "
        "Four sensors are a cost/information tradeoff on this simulator, not a globally optimal layout.",
        "",
        _md(ablation, keep_ab),
        "## 6.4 Robustness",
        "",
        f"Held-out-subject baseline macro-F1 is **{_d(reg, 'holdout_baseline_macro_f1')}** (a different estimand from 5-fold OOF). "
        f"Simulated 30% packet loss: **{_d(reg, 'packet_loss_30pct_macro_f1')}**. "
        f"Gaussian noise SD 12 kPa: **{_d(reg, 'noise_12kpa_macro_f1')}**. "
        f"Missing heel channel: **{_d(reg, 'missing_heel_macro_f1')}**. "
        f"Constant +15 kPa bias: **{_d(reg, 'bias_15kpa_macro_f1')}**.",
        "",
        _md(robust_pub) if robust_pub else _md(packet),
        "## 6.5 Sampling rate (no fake upsampling)",
        "",
        f"Training remains at 25 Hz. Testing on a 50% subsample (original samples only) yields macro-F1 "
        f"**{_d(reg, 'sampling_50pct_macro_f1')}**.",
        "",
        _md(sampling, ["label", "effective_hz", "macro_f1", "ble_bytes_per_s_two_feet", "note"]),
        "## 6.6 Repeatability",
        "",
        "X-Step four-site test–retest ICC is **not reported** (no repeated 4-FSR walking sessions). "
        "Simulator CVs characterize the generator only. M1–M10 in the 32-cell archive are unlabeled takes, not identical repeats.",
        "",
        _md(_round_rows(_rows("repeatability.csv"), ["within_session_cv_median", "between_seed_icc"])),
        "## 6.7 Sensor calibration vs ML accuracy",
        "",
        "These quantities are not interchangeable. Four-site log–log reconstruction on "
        f"operator-attested `data/calibration/four_site_fsr_bench.csv` (480 load–unload rows; not walking data): "
        f"MAE **{_d(reg, 'calibration_mae_n')}**, RMSE **{_d(reg, 'calibration_rmse_n')}**. "
        "Lab photographs of the rig are not in the repository.",
        "",
        "## 6.8 Host latency (radio not measured)",
        "",
        f"Combined host path mean **{_d(reg, 'host_path_mean_ms')}** (P95 **{_d(reg, 'host_path_p95_ms')}**). "
        f"Firmware sample period is {_d(reg, 'firmware_sample_period_ms')} by design. BLE airtime is unmeasured. "
        f"Serialized logreg size **{_d(reg, 'logreg_serialized_kb')}**.",
        "",
        _md(deploy),
        "## 6.9 Probability calibration",
        "",
        f"OOF ECE **{_d(reg, 'logreg_grouped_ece')}**, AUROC **{_d(reg, 'logreg_grouped_auroc')}**. "
        "Platt scaling was fit on inner training groups only and is **not** adopted as the production calibrator.",
        "",
        "## 6.10 Thresholds",
        "",
        "Peak-pressure cut-offs are **engineering risk-alert operating points** on synthetic non-normal vs normal labels, "
        "not medically validated ulcer thresholds.",
        "",
        _md(_round_rows(_rows("threshold_sweep.csv"), ["threshold_kpa", "sensitivity", "specificity", "false_alert_rate", "missed_event_rate"])),
        "## 6.11 Window duration (same-fs train/test)",
        "",
        _md(_round_rows(_rows("window_fs.csv"), ["sample_hz", "window_seconds", "macro_f1"])),
        "",
        "The frozen 4 s / 25 Hz window is a compromise between cadence estimates and alert latency.",
        "",
        "## 6.12 Human 32-cell walking (not X-Step FSR)",
        "",
        f"**{_d(reg, 'n_subjects_human_32site')}** adults, **{_d(reg, 'n_takes_human_32site')}** analyzed takes "
        "(150 unique pressure takes, one excluded for insole desynchronization). "
        "Hardware is a 32-cell instrumented insole synchronized to OptiTrack, **not** the four-site FSR402 prototype. "
        f"Median anteroposterior CoP correlation (4 anatomical sites vs native 32-cell CoP): **{_d(reg, 'human_32site_copy_r')}**. "
        f"Mediolateral CoP is not recovered (**{_d(reg, 'human_32site_copx_r')}**). "
        f"Single-site vs regional-max time-series *r*: MET1 {_d(reg, 'human_32site_met1_timeseries_r')}, "
        f"MET2 {_d(reg, 'human_32site_met2_timeseries_r')}, MET5 {_d(reg, 'human_32site_met5_timeseries_r')}, "
        f"HEEL {_d(reg, 'human_32site_heel_timeseries_r')}. "
        f"Median overground speed **{_d(reg, 'human_32site_speed_m_s')}** under a 64 Hz timestamp assumption. "
        "These numbers are not mixed into the frozen synthetic gait macro-F1 tables.",
        "",
        _md(_round_rows(_rows("human_optitrack_sparse_vs_dense.csv"), ["site", "n_foot_takes", "median_timeseries_r", "peak_peak_r", "peak_nrmse", "data_source", "hardware"])),
        "",
    ]
    text = "\n".join(parts)
    verify_text_contains(text, "0.885")
    OUT.write_text(text)
    SNIP.write_text(
        "\n".join(
            [
                f"- grouped logreg macro-F1: {logreg_disp}",
                f"- four-site ablation F1: {_d(reg, 'ablation_4site_macro_f1')}",
                f"- drop MET5 F1: {_d(reg, 'ablation_drop_met5_macro_f1')}",
                f"- drop HEEL F1: {_d(reg, 'ablation_drop_heel_macro_f1')}",
                f"- 30% packet-loss F1: {_d(reg, 'packet_loss_30pct_macro_f1')}",
                f"- host path mean: {_d(reg, 'host_path_mean_ms')}",
                f"- 32-cell walking subjects: {_d(reg, 'n_subjects_human_32site')}",
                f"- 4-site vs dense AP CoP r: {_d(reg, 'human_32site_copy_r')}",
                "",
            ]
        )
    )
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
