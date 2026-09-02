#!/usr/bin/env python3
"""Evaluate the operator-provided 32-cell insole + OptiTrack walking archive.

Does not retrain gait models. Does not treat the archive as X-Step FSR402 walking.
"""

from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("MPLCONFIGDIR", str(_ROOT / ".mplconfig"))
os.environ.setdefault("MPLBACKEND", "Agg")
(_ROOT / ".mplconfig").mkdir(exist_ok=True)
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import matplotlib.pyplot as plt
import numpy as np

from research.insoles_optitrack import (
    SITES,
    evaluate_archive,
    four_site_series,
    load_layout,
    load_pressure_side,
    pressure_csv_name,
)
import zipfile

OUT = _ROOT / "research" / "results" / "human_optitrack_evaluation.json"
TAB = _ROOT / "research" / "tables" / "human_optitrack_sparse_vs_dense.csv"
TAKE_CSV = _ROOT / "research" / "tables" / "human_optitrack_takes.csv"
FIG = _ROOT / "research" / "figures"
CAPTION = (
    "32-cell instrumented insole during overground walking (not the X-Step four-site FSR402 prototype). "
    "Native counts 0–4096."
)

DEFAULT_ZIPS = [
    Path(os.environ["XSTEP_OPTITRACK_ZIP"]) if os.environ.get("XSTEP_OPTITRACK_ZIP") else None,
    _ROOT / "data" / "raw" / "InsolesOpitrackDataset.zip",
    Path.home() / "Downloads" / "InsolesOpitrackDataset.zip",
]


def find_zip() -> Path:
    for p in DEFAULT_ZIPS:
        if p is not None and p.is_file():
            return p
    raise FileNotFoundError(
        "InsolesOpitrackDataset.zip not found. Set XSTEP_OPTITRACK_ZIP or place the zip under data/raw/."
    )


def _write_tables(payload: dict) -> None:
    TAB.parent.mkdir(parents=True, exist_ok=True)
    with TAB.open("w", newline="") as f:
        fields = [
            "site",
            "n_foot_takes",
            "median_timeseries_r",
            "peak_peak_r",
            "peak_rmse_counts",
            "peak_nrmse",
            "median_sparse_peak",
            "median_dense_peak",
            "data_source",
            "hardware",
        ]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in payload["per_region"]:
            w.writerow(
                {
                    **{k: (f"{v:.4f}" if isinstance(v, float) else v) for k, v in row.items()},
                    "data_source": "human",
                    "hardware": "32-cell insole, not X-Step 4-FSR",
                }
            )
    slim_fields = [
        "subject_id",
        "take_id",
        "n_samples",
        "n_motion_frames",
        "motion_pressure_ratio",
        "speed_m_s_assumed_64hz",
        "left_n_steps",
        "right_n_steps",
        "left_copy_r",
        "right_copy_r",
        "exclude_pressure",
        "exclude_mocap",
    ]
    with TAKE_CSV.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=slim_fields, extrasaction="ignore")
        w.writeheader()
        for row in payload["takes"]:
            w.writerow({k: row.get(k, "") for k in slim_fields})


def _figures(payload: dict, zip_path: Path) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    analyzed = [r for r in payload["takes"] if r.get("n_samples") and not r.get("exclude_pressure")]
    fig, axes = plt.subplots(2, 2, figsize=(8.2, 6.8))
    axes = axes.ravel()
    for ax, site in zip(axes, SITES):
        s, d = [], []
        for r in analyzed:
            for side in ("left", "right"):
                s.append(r[f"{side}_{site}_sparse_peak"])
                d.append(r[f"{side}_{site}_dense_peak"])
        ax.scatter(d, s, s=12, alpha=0.45, c="#1f4e79")
        lim = max(max(d), max(s))
        ax.plot([0, lim], [0, lim], color="#888", lw=1, ls="--")
        ax.set_title(site.upper())
        ax.set_xlabel("Region-max peak (counts)")
        ax.set_ylabel("Single-site peak (counts)")
    fig.suptitle(f"Four anatomical sites vs dense regional peaks\n{CAPTION}")
    fig.tight_layout()
    for ext in (".png", ".pdf", ".svg"):
        fig.savefig(FIG / f"fig14_human_sparse_vs_dense{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)

    # Example traces: first analyzed take
    layout = load_layout()
    example = next((r for r in analyzed if r["subject_id"] == "P1" and r["take_id"] == "M1"), analyzed[0])
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        ln = pressure_csv_name(names, example["subject_id"], example["take_id"], "L")
        left = load_pressure_side(zf, ln)
    four = four_site_series(left["pressure"], layout, "left")
    hz = float(payload["assumed_insole_hz"])
    t = np.arange(left["n"]) / hz
    fig, ax = plt.subplots(figsize=(7.4, 3.8))
    for site in SITES:
        ax.plot(t, four[site], label=site.upper(), lw=1.1)
    ax.set_xlabel(f"Time (s) at assumed {hz:.0f} Hz")
    ax.set_ylabel("Native insole counts")
    ax.legend(frameon=False, ncol=4, fontsize=8)
    ax.set_title(
        f"Left-foot four-site subsample, {example['subject_id']} {example['take_id']}\n{CAPTION}"
    )
    fig.tight_layout()
    for ext in (".png", ".pdf", ".svg"):
        fig.savefig(FIG / f"fig15_human_walking_traces{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)


def public_payload(payload: dict) -> dict:
    """Drop per-take bulk from the registry-facing JSON (keep summary)."""
    keep = dict(payload)
    keep["n_take_rows"] = len(payload.get("takes") or [])
    keep.pop("takes", None)
    demo = dict(keep.get("demographics_aggregate") or {})
    demo.pop("subject_codes", None)
    keep["demographics_aggregate"] = demo
    return keep


def main() -> None:
    zip_path = find_zip()
    payload = evaluate_archive(zip_path)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    summary = public_payload(payload)
    OUT.write_text(json.dumps(summary, indent=2, default=str) + "\n")
    _write_tables(payload)
    _figures(payload, zip_path)
    print(
        json.dumps(
            {
                "n_subjects": payload["n_subjects"],
                "n_takes_analyzed": payload["n_takes_analyzed"],
                "median_copy_r": payload["median_copy_r"],
                "median_speed_m_s_assumed_64hz": payload["median_speed_m_s_assumed_64hz"],
                "icc_sumP": payload["within_subject_icc"].get("sumP"),
                "source_zip_sha256": payload["source_zip_sha256"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
