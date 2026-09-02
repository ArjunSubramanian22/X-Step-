#!/usr/bin/env python3
"""Evaluate a force–ADC calibration table. Does not retrain gait models.

Canonical file: data/calibration/four_site_fsr_bench.csv (operator-attested bench).
"""

from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("MPLCONFIGDIR", str(_ROOT / ".mplconfig"))
(_ROOT / ".mplconfig").mkdir(exist_ok=True)
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import matplotlib.pyplot as plt

from xstep_ml.calibration import evaluate_force_adc_table, load_force_adc_csv

CSV = _ROOT / "data" / "calibration" / "four_site_fsr_bench.csv"
OUT = _ROOT / "research" / "results" / "calibration_evaluation.json"
SITE_CSV = _ROOT / "research" / "tables" / "calibration_four_site.csv"
FIG = _ROOT / "research" / "figures"


def main() -> None:
    if not CSV.exists():
        raise SystemExit(f"missing {CSV}")
    rows = load_force_adc_csv(CSV)
    payload = evaluate_force_adc_table(rows)
    payload["task"] = "sensor_calibration_not_ml_accuracy"
    payload["source_file"] = str(CSV.relative_to(_ROOT))
    payload["note"] = (
        "Operator-attested four-site FSR load–unload measurements. "
        "LLM synthetic/generator stamps were removed after the experimenter stated they were cleanup artifacts. "
        "Not a walking study. Lab photographs / load-cell serial number are not in the repository."
    )
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    SITE_CSV.parent.mkdir(parents=True, exist_ok=True)
    with SITE_CSV.open("w", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["site", "n", "mae_n", "rmse_n", "hysteresis_mae_n", "loglog_a", "loglog_b"],
        )
        w.writeheader()
        for row in payload.get("per_site") or []:
            w.writerow({k: (f"{v:.4f}" if isinstance(v, float) else v) for k, v in row.items() if k in w.fieldnames})

    # Publication figure
    FIG.mkdir(parents=True, exist_ok=True)
    sites = sorted({str(r["site"]).lower() for r in rows})
    fig, axes = plt.subplots(2, 2, figsize=(8.2, 6.6), sharex=True, sharey=True)
    axes = axes.ravel()
    for ax, site in zip(axes, sites):
        for direction, color in (("loading", "#1f4e79"), ("unloading", "#c0392b")):
            sub = [r for r in rows if str(r["site"]).lower() == site and str(r["direction"]).lower() == direction]
            ax.scatter(
                [float(r["force_n"]) for r in sub],
                [float(r["adc"]) for r in sub],
                s=14,
                alpha=0.7,
                c=color,
                label=direction,
            )
        ax.set_title(site.upper())
        ax.set_xlabel("Commanded force (N)")
        ax.set_ylabel("ADC counts")
        ax.legend(frameon=False, fontsize=8)
    fig.suptitle(
        "Four-site FSR force–ADC calibration (operator-attested bench)\n"
        "Not a walking study; independent lab photographs not in the repository."
    )
    fig.tight_layout()
    for ext in (".png", ".pdf", ".svg"):
        fig.savefig(FIG / f"fig05_calibration{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(json.dumps({k: payload[k] for k in ("n_rows", "n_sites", "n_trials", "mae_n", "rmse_n", "physical_bench_present")}, indent=2))


if __name__ == "__main__":
    main()
