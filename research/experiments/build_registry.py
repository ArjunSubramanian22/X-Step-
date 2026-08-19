#!/usr/bin/env python3
"""Build research/results/final_results_registry.json from stored experiment files.

Does not retrain. Display rounding is 3 decimals for rates/F1, 2 for latency ms and force N.
"""

from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
TAB = _ROOT / "research" / "tables"
RES = _ROOT / "research" / "results"
OUT = RES / "final_results_registry.json"
PUB = TAB / "publication"


def _git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=_ROOT, stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return "unknown"


def _rows(name: str) -> list[dict]:
    path = TAB / name
    if not path.exists():
        return []
    with path.open() as f:
        return list(csv.DictReader(f))


def _f(x, nd: int | None = None) -> float | None:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    if nd is None:
        return v
    return round(v, nd)


def _entry(
    *,
    key: str,
    metric: str,
    value,
    ci=None,
    model: str | None = None,
    experiment: str,
    dataset: str,
    split: str,
    n_subjects: int | None,
    n_sessions: int | None,
    synthetic_or_real: str,
    result_file: str,
    extra: dict | None = None,
) -> dict:
    rec = {
        "key": key,
        "metric": metric,
        "value": value,
        "display": None,
        "confidence_interval": ci,
        "model": model,
        "experiment": experiment,
        "dataset": dataset,
        "split": split,
        "n_subjects": n_subjects,
        "n_sessions": n_sessions,
        "synthetic_or_real": synthetic_or_real,
        "result_file": result_file,
        "git_sha_recorded_with_source": None,
    }
    if isinstance(value, float):
        rec["display"] = f"{value:.3f}" if abs(value) < 10 else f"{value:.2f}"
    elif value is None:
        rec["display"] = "n/a"
    else:
        rec["display"] = str(value)
    if extra:
        rec.update(extra)
    return rec


def _write_pub_csv(name: str, rows: list[dict], fields: list[str]) -> None:
    PUB.mkdir(parents=True, exist_ok=True)
    path = PUB / name
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            out = {}
            for k in fields:
                v = r.get(k, "")
                if isinstance(v, float):
                    out[k] = f"{v:.3f}"
                else:
                    out[k] = v
            w.writerow(out)


def main() -> dict:
    models = _rows("model_comparison.csv") or _rows("table3_model_comparison.csv")
    ablation = _rows("sensor_ablation_publication.csv") or _rows("table4_sensor_ablation.csv")
    splits = _rows("split_protocol_comparison.csv")
    packet = _rows("packet_loss_sweep.csv")
    sampling = _rows("sampling_rate_tradeoff.csv")
    robust = _rows("table5_robustness.csv")
    logreg = next((r for r in models if r.get("model") == "logreg"), {})
    four = next((r for r in ablation if r.get("subset") == "4_all"), {})
    no_met5 = next((r for r in ablation if r.get("subset") == "3_no_met5"), {})
    no_heel = next((r for r in ablation if r.get("subset") == "3_no_heel"), {})
    no_met1 = next((r for r in ablation if r.get("subset") == "3_no_met1"), {})
    one = next((r for r in ablation if r.get("subset") == "1_met2"), {})
    iid = next((r for r in splits if r.get("protocol") == "iid_window"), {})
    subj = next((r for r in splits if r.get("protocol") == "subject"), {})
    sess = next((r for r in splits if r.get("protocol") == "session"), {})
    pkt30 = next((r for r in packet if str(r.get("severity")) in ("0.3", "0.30")), {})
    samp50 = next((r for r in sampling if str(r.get("keep_fraction")) in ("0.5", "0.50")), {})
    noise12 = next((r for r in robust if r.get("perturbation") == "gaussian_noise_kpa" and str(r.get("severity")) == "12.0"), {})
    miss_heel = next((r for r in robust if r.get("perturbation") == "missing_sensor_index" and str(r.get("severity")) == "3.0"), {})
    bias15 = next((r for r in robust if r.get("perturbation") == "sensor_bias_kpa" and str(r.get("severity")) == "15.0"), {})
    none_h = next((r for r in robust if r.get("perturbation") == "none"), {})
    cal = json.loads((RES / "calibration_evaluation.json").read_text()) if (RES / "calibration_evaluation.json").exists() else {}
    lat = json.loads((RES / "latency_host.json").read_text()) if (RES / "latency_host.json").exists() else {}
    proba = json.loads((RES / "probability_calibration.json").read_text()) if (RES / "probability_calibration.json").exists() else {}
    man = json.loads((RES / "manifest.json").read_text()) if (RES / "manifest.json").exists() else {}
    n_subj = int(man.get("n_subjects") or logreg.get("n_subjects") or 24)
    n_win = int(man.get("n_windows") or logreg.get("n_windows") or 2592)

    entries = [
        _entry(
            key="n_windows",
            metric="n_windows",
            value=n_win,
            experiment="synthetic_cohort",
            dataset="synthetic_4fsr_gait",
            split="n/a",
            n_subjects=n_subj,
            n_sessions=216,
            synthetic_or_real="synthetic",
            result_file="research/results/manifest.json",
        ),
        _entry(
            key="n_subjects_virtual",
            metric="n_subjects",
            value=n_subj,
            experiment="synthetic_cohort",
            dataset="synthetic_4fsr_gait",
            split="n/a",
            n_subjects=n_subj,
            n_sessions=216,
            synthetic_or_real="synthetic",
            result_file="research/results/manifest.json",
        ),
        _entry(
            key="n_subjects_human",
            metric="n_subjects",
            value=0,
            experiment="data_inventory",
            dataset="human_walking_fsr",
            split="n/a",
            n_subjects=0,
            n_sessions=0,
            synthetic_or_real="real",
            result_file="research/data_inventory.json",
        ),
        _entry(
            key="logreg_grouped_macro_f1",
            metric="macro_f1",
            value=_f(logreg.get("macro_f1")),
            ci={"lo": _f(logreg.get("macro_f1_ci95_lo")), "hi": _f(logreg.get("macro_f1_ci95_hi")), "method": "percentile_bootstrap"},
            model="logreg",
            experiment="groupkfold_subject_oof",
            dataset="synthetic_4fsr_gait",
            split="GroupKFold-subject",
            n_subjects=n_subj,
            n_sessions=216,
            synthetic_or_real="synthetic",
            result_file="research/tables/model_comparison.csv",
        ),
        _entry(
            key="logreg_grouped_auroc",
            metric="auroc_macro",
            value=_f(logreg.get("auroc_macro") or proba.get("auroc_oof")),
            model="logreg",
            experiment="groupkfold_subject_oof",
            dataset="synthetic_4fsr_gait",
            split="GroupKFold-subject",
            n_subjects=n_subj,
            n_sessions=216,
            synthetic_or_real="synthetic",
            result_file="research/results/probability_calibration.json",
        ),
        _entry(
            key="logreg_grouped_ece",
            metric="ece",
            value=_f(proba.get("ece_oof")),
            model="logreg",
            experiment="groupkfold_subject_oof",
            dataset="synthetic_4fsr_gait",
            split="GroupKFold-subject",
            n_subjects=n_subj,
            n_sessions=216,
            synthetic_or_real="synthetic",
            result_file="research/results/probability_calibration.json",
        ),
        _entry(
            key="iid_macro_f1",
            metric="macro_f1",
            value=_f(iid.get("macro_f1")),
            ci={"lo": _f(iid.get("macro_f1_ci95_lo")), "hi": _f(iid.get("macro_f1_ci95_hi"))},
            model="logreg",
            experiment="split_protocol",
            dataset="synthetic_4fsr_gait",
            split="iid_window",
            n_subjects=n_subj,
            n_sessions=216,
            synthetic_or_real="synthetic",
            result_file="research/tables/split_protocol_comparison.csv",
            extra={"note": "optimistic control; subject leakage possible"},
        ),
        _entry(
            key="session_macro_f1",
            metric="macro_f1",
            value=_f(sess.get("macro_f1")),
            model="logreg",
            experiment="split_protocol",
            dataset="synthetic_4fsr_gait",
            split="GroupKFold-session",
            n_subjects=n_subj,
            n_sessions=216,
            synthetic_or_real="synthetic",
            result_file="research/tables/split_protocol_comparison.csv",
        ),
        _entry(
            key="ablation_4site_macro_f1",
            metric="macro_f1",
            value=_f(four.get("Performance") or four.get("macro_f1")),
            model="logreg",
            experiment="sensor_ablation",
            dataset="synthetic_4fsr_gait",
            split="GroupKFold-subject",
            n_subjects=n_subj,
            n_sessions=216,
            synthetic_or_real="synthetic",
            result_file="research/tables/sensor_ablation_publication.csv",
        ),
        _entry(
            key="ablation_drop_met5_macro_f1",
            metric="macro_f1",
            value=_f(no_met5.get("Performance") or no_met5.get("macro_f1")),
            model="logreg",
            experiment="sensor_ablation",
            dataset="synthetic_4fsr_gait",
            split="GroupKFold-subject",
            n_subjects=n_subj,
            n_sessions=216,
            synthetic_or_real="synthetic",
            result_file="research/tables/sensor_ablation_publication.csv",
        ),
        _entry(
            key="ablation_drop_heel_macro_f1",
            metric="macro_f1",
            value=_f(no_heel.get("Performance") or no_heel.get("macro_f1")),
            model="logreg",
            experiment="sensor_ablation",
            dataset="synthetic_4fsr_gait",
            split="GroupKFold-subject",
            n_subjects=n_subj,
            n_sessions=216,
            synthetic_or_real="synthetic",
            result_file="research/tables/sensor_ablation_publication.csv",
        ),
        _entry(
            key="ablation_drop_met1_macro_f1",
            metric="macro_f1",
            value=_f(no_met1.get("Performance") or no_met1.get("macro_f1")),
            model="logreg",
            experiment="sensor_ablation",
            dataset="synthetic_4fsr_gait",
            split="GroupKFold-subject",
            n_subjects=n_subj,
            n_sessions=216,
            synthetic_or_real="synthetic",
            result_file="research/tables/sensor_ablation_publication.csv",
        ),
        _entry(
            key="ablation_1site_met2_macro_f1",
            metric="macro_f1",
            value=_f(one.get("Performance") or one.get("macro_f1")),
            model="logreg",
            experiment="sensor_ablation",
            dataset="synthetic_4fsr_gait",
            split="GroupKFold-subject",
            n_subjects=n_subj,
            n_sessions=216,
            synthetic_or_real="synthetic",
            result_file="research/tables/sensor_ablation_publication.csv",
        ),
        _entry(
            key="holdout_baseline_macro_f1",
            metric="macro_f1",
            value=_f(none_h.get("macro_f1") or next((r.get("macro_f1") for r in packet if str(r.get("severity")) in ("0.0", "0")), None)),
            model="logreg",
            experiment="robustness_holdout",
            dataset="synthetic_4fsr_gait",
            split="grouped_holdout_25pct_subjects",
            n_subjects=n_subj,
            n_sessions=216,
            synthetic_or_real="synthetic",
            result_file="research/tables/table5_robustness.csv",
            extra={"note": "Not the same estimand as 5-fold OOF macro-F1"},
        ),
        _entry(
            key="packet_loss_30pct_macro_f1",
            metric="macro_f1",
            value=_f(pkt30.get("macro_f1")),
            model="logreg",
            experiment="packet_loss_sweep",
            dataset="synthetic_4fsr_gait",
            split="grouped_holdout_25pct_subjects",
            n_subjects=n_subj,
            n_sessions=216,
            synthetic_or_real="synthetic",
            result_file="research/tables/packet_loss_sweep.csv",
        ),
        _entry(
            key="noise_12kpa_macro_f1",
            metric="macro_f1",
            value=_f(noise12.get("macro_f1")),
            model="logreg",
            experiment="robustness_holdout",
            dataset="synthetic_4fsr_gait",
            split="grouped_holdout_25pct_subjects",
            n_subjects=n_subj,
            n_sessions=216,
            synthetic_or_real="synthetic",
            result_file="research/tables/table5_robustness.csv",
        ),
        _entry(
            key="missing_heel_macro_f1",
            metric="macro_f1",
            value=_f(miss_heel.get("macro_f1")),
            model="logreg",
            experiment="robustness_holdout",
            dataset="synthetic_4fsr_gait",
            split="grouped_holdout_25pct_subjects",
            n_subjects=n_subj,
            n_sessions=216,
            synthetic_or_real="synthetic",
            result_file="research/tables/table5_robustness.csv",
        ),
        _entry(
            key="bias_15kpa_macro_f1",
            metric="macro_f1",
            value=_f(bias15.get("macro_f1")),
            model="logreg",
            experiment="robustness_holdout",
            dataset="synthetic_4fsr_gait",
            split="grouped_holdout_25pct_subjects",
            n_subjects=n_subj,
            n_sessions=216,
            synthetic_or_real="synthetic",
            result_file="research/tables/table5_robustness.csv",
        ),
        _entry(
            key="sampling_50pct_macro_f1",
            metric="macro_f1",
            value=_f(samp50.get("macro_f1")),
            model="logreg",
            experiment="sampling_rate_tradeoff",
            dataset="synthetic_4fsr_gait",
            split="grouped_holdout_25pct_subjects",
            n_subjects=n_subj,
            n_sessions=216,
            synthetic_or_real="synthetic",
            result_file="research/tables/sampling_rate_tradeoff.csv",
        ),
        _entry(
            key="calibration_mae_n",
            metric="mae_n",
            value=_f(cal.get("mae_n")),
            experiment="calibration_simulated_example",
            dataset="calibration_simulated_example",
            split="n/a",
            n_subjects=0,
            n_sessions=0,
            synthetic_or_real="synthetic",
            result_file="research/results/calibration_evaluation.json",
            extra={"display": f"{float(cal['mae_n']):.2f} N" if cal.get("mae_n") is not None else "n/a", "physical_bench": False},
        ),
        _entry(
            key="calibration_rmse_n",
            metric="rmse_n",
            value=_f(cal.get("rmse_n")),
            experiment="calibration_simulated_example",
            dataset="calibration_simulated_example",
            split="n/a",
            n_subjects=0,
            n_sessions=0,
            synthetic_or_real="synthetic",
            result_file="research/results/calibration_evaluation.json",
            extra={"display": f"{float(cal['rmse_n']):.2f} N" if cal.get("rmse_n") is not None else "n/a"},
        ),
        _entry(
            key="host_path_mean_ms",
            metric="latency_ms",
            value=_f(lat.get("host_path_mean_ms")),
            model="logreg",
            experiment="host_latency",
            dataset="n/a",
            split="n/a",
            n_subjects=None,
            n_sessions=None,
            synthetic_or_real="host_cpu",
            result_file="research/results/latency_host.json",
            extra={"display": f"{float(lat['host_path_mean_ms']):.2f} ms" if lat.get("host_path_mean_ms") is not None else "n/a"},
        ),
        _entry(
            key="host_path_p95_ms",
            metric="latency_ms",
            value=_f(lat.get("host_path_p95_ms")),
            model="logreg",
            experiment="host_latency",
            dataset="n/a",
            split="n/a",
            n_subjects=None,
            n_sessions=None,
            synthetic_or_real="host_cpu",
            result_file="research/results/latency_host.json",
        ),
        _entry(
            key="logreg_serialized_kb",
            metric="serialized_kb",
            value=_f(logreg.get("serialized_kb")),
            model="logreg",
            experiment="efficiency",
            dataset="synthetic_4fsr_gait",
            split="n/a",
            n_subjects=n_subj,
            n_sessions=216,
            synthetic_or_real="synthetic",
            result_file="research/tables/model_comparison.csv",
        ),
        _entry(
            key="sample_hz",
            metric="hz",
            value=25.0,
            experiment="firmware_spec",
            dataset="n/a",
            split="n/a",
            n_subjects=None,
            n_sessions=None,
            synthetic_or_real="spec",
            result_file="firmware/xstep_insole/xstep_insole.ino",
        ),
        _entry(
            key="ble_payload_bytes",
            metric="bytes",
            value=28,
            experiment="protocol",
            dataset="n/a",
            split="n/a",
            n_subjects=None,
            n_sessions=None,
            synthetic_or_real="spec",
            result_file="xstep_ml/protocol.py",
        ),
        _entry(
            key="feature_count",
            metric="n_features",
            value=59,
            experiment="biomechanics",
            dataset="n/a",
            split="n/a",
            n_subjects=None,
            n_sessions=None,
            synthetic_or_real="spec",
            result_file="xstep_ml/biomechanics.py",
        ),
        _entry(
            key="heuristic_macro_f1",
            metric="macro_f1",
            value=_f(next((r.get("macro_f1") for r in models if r.get("model") == "threshold_heuristic"), None)),
            model="threshold_heuristic",
            experiment="groupkfold_subject_oof",
            dataset="synthetic_4fsr_gait",
            split="GroupKFold-subject",
            n_subjects=n_subj,
            n_sessions=216,
            synthetic_or_real="synthetic",
            result_file="research/tables/model_comparison.csv",
        ),
        _entry(
            key="hist_gbm_grouped_macro_f1",
            metric="macro_f1",
            value=_f(next((r.get("macro_f1") for r in models if r.get("model") == "hist_gbm"), None)),
            model="hist_gbm",
            experiment="groupkfold_subject_oof",
            dataset="synthetic_4fsr_gait",
            split="GroupKFold-subject",
            n_subjects=n_subj,
            n_sessions=216,
            synthetic_or_real="synthetic",
            result_file="research/tables/model_comparison.csv",
        ),
        _entry(
            key="majority_macro_f1",
            metric="macro_f1",
            value=_f(next((r.get("macro_f1") for r in models if r.get("model") == "majority"), None)),
            model="majority",
            experiment="groupkfold_subject_oof",
            dataset="synthetic_4fsr_gait",
            split="GroupKFold-subject",
            n_subjects=n_subj,
            n_sessions=216,
            synthetic_or_real="synthetic",
            result_file="research/tables/model_comparison.csv",
        ),
        _entry(
            key="peak_only_macro_f1",
            metric="macro_f1",
            value=_f(next((r.get("macro_f1") for r in _rows("feature_ablation.csv") if r.get("feature_set") == "peak_only"), None)),
            model="logreg",
            experiment="feature_ablation",
            dataset="synthetic_4fsr_gait",
            split="GroupKFold-subject",
            n_subjects=n_subj,
            n_sessions=216,
            synthetic_or_real="synthetic",
            result_file="research/tables/feature_ablation.csv",
            extra={"note": "Peak-only features nearly match the 59-D set on this simulator"},
        ),
        _entry(
            key="delta_iid_minus_subject_f1",
            metric="delta_macro_f1",
            value=_f((_f(iid.get("macro_f1")) or 0) - (_f(subj.get("macro_f1") or logreg.get("macro_f1")) or 0)),
            model="logreg",
            experiment="split_protocol",
            dataset="synthetic_4fsr_gait",
            split="iid_minus_subject",
            n_subjects=n_subj,
            n_sessions=216,
            synthetic_or_real="synthetic",
            result_file="research/tables/split_protocol_comparison.csv",
        ),
        _entry(
            key="delta_drop_met5_f1",
            metric="delta_macro_f1",
            value=_f(
                (_f(no_met5.get("Performance") or no_met5.get("macro_f1")) or 0)
                - (_f(four.get("Performance") or four.get("macro_f1")) or 0)
            ),
            model="logreg",
            experiment="sensor_ablation",
            dataset="synthetic_4fsr_gait",
            split="GroupKFold-subject",
            n_subjects=n_subj,
            n_sessions=216,
            synthetic_or_real="synthetic",
            result_file="research/tables/sensor_ablation_publication.csv",
        ),
        _entry(
            key="delta_drop_heel_f1",
            metric="delta_macro_f1",
            value=_f(
                (_f(no_heel.get("Performance") or no_heel.get("macro_f1")) or 0)
                - (_f(four.get("Performance") or four.get("macro_f1")) or 0)
            ),
            model="logreg",
            experiment="sensor_ablation",
            dataset="synthetic_4fsr_gait",
            split="GroupKFold-subject",
            n_subjects=n_subj,
            n_sessions=216,
            synthetic_or_real="synthetic",
            result_file="research/tables/sensor_ablation_publication.csv",
        ),
        _entry(
            key="firmware_sample_period_ms",
            metric="latency_ms",
            value=40.0,
            experiment="firmware_spec",
            dataset="n/a",
            split="n/a",
            n_subjects=None,
            n_sessions=None,
            synthetic_or_real="spec",
            result_file="firmware/xstep_insole/xstep_insole.ino",
            extra={"display": "40 ms"},
        ),
    ]
    # Canonical display strings used by the manuscript (3 decimals for rates).
    for e in entries:
        if e["key"] == "logreg_grouped_macro_f1" and e.get("value") is not None and e.get("confidence_interval"):
            ci = e["confidence_interval"]
            e["display"] = f"{e['value']:.3f} [95% CI: {ci['lo']:.3f}–{ci['hi']:.3f}]"
        elif e["metric"] == "macro_f1" and isinstance(e.get("value"), float):
            e["display"] = f"{e['value']:.3f}"
        elif e["key"] == "logreg_grouped_auroc" and isinstance(e.get("value"), float):
            e["display"] = f"{e['value']:.3f}"
        elif e["key"] == "logreg_grouped_ece" and isinstance(e.get("value"), float):
            e["display"] = f"{e['value']:.3f}"
        elif e["key"] == "host_path_mean_ms" and isinstance(e.get("value"), float):
            e["display"] = f"{e['value']:.2f} ms"
        elif e["key"] == "host_path_p95_ms" and isinstance(e.get("value"), float):
            e["display"] = f"{e['value']:.2f} ms"
        elif e["key"] == "calibration_mae_n" and isinstance(e.get("value"), float):
            e["display"] = f"{e['value']:.2f} N"
        elif e["key"] == "calibration_rmse_n" and isinstance(e.get("value"), float):
            e["display"] = f"{e['value']:.2f} N"
        elif e["key"] == "logreg_serialized_kb" and isinstance(e.get("value"), float):
            e["display"] = f"{e['value']:.1f} kB"

    by_key = {e["key"]: e for e in entries if e.get("key")}
    payload = {
        "built_utc": datetime.now(timezone.utc).isoformat(),
        "git_sha": _git_sha(),
        "does_not_retrain": True,
        "rounding": {"rates": 3, "latency_ms": 2, "force_n": 2},
        "dataset_hash": man.get("dataset_hash"),
        "entries": entries,
        "by_key": by_key,
    }
    OUT.write_text(json.dumps(payload, indent=2, default=str))

    # publication-rounded robustness summary
    base = _f(none_h.get("macro_f1")) or 0.0
    summary_rows = []

    def add_sum(name, sev, val, src):
        v = _f(val)
        if v is None:
            return
        summary_rows.append(
            {
                "perturbation": name,
                "severity": sev,
                "baseline_macro_f1": f"{base:.3f}",
                "perturbed_macro_f1": f"{v:.3f}",
                "relative_change": f"{(v - base) / base:.3f}" if base else "",
                "source": src,
                "data_source": "synthetic",
            }
        )

    add_sum("none", "0", none_h.get("macro_f1"), "table5_robustness.csv")
    add_sum("gaussian_noise_kpa", "12", noise12.get("macro_f1"), "table5_robustness.csv")
    add_sum("dropped_packets_frac", "0.30", pkt30.get("macro_f1"), "packet_loss_sweep.csv")
    add_sum("missing_channel_heel", "heel=0", miss_heel.get("macro_f1"), "table5_robustness.csv")
    add_sum("sensor_bias_kpa", "15", bias15.get("macro_f1"), "table5_robustness.csv")
    add_sum("sampling_keep_frac", "0.50", samp50.get("macro_f1"), "sampling_rate_tradeoff.csv")
    _write_pub_csv(
        "table_V_robustness_summary.csv",
        summary_rows,
        ["perturbation", "severity", "baseline_macro_f1", "perturbed_macro_f1", "relative_change", "source", "data_source"],
    )
    print(json.dumps({"wrote": str(OUT), "n_entries": len(entries)}, indent=2))
    return payload


if __name__ == "__main__":
    main()
