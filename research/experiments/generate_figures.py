#!/usr/bin/env python3
"""Publication figures (PNG + PDF + SVG) from experiment result files."""

from __future__ import annotations

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
import numpy as np
import seaborn as sns

from xstep_ml.data.synthetic_gait import synthesize_window
from xstep_ml.hardware import SITE_LABELS, SensorSite

RES = _ROOT / "research" / "results" / "research_results.json"
FIG = _ROOT / "research" / "figures"
DPI = 300
CAPTION_SYN = "Synthetic / engineering validation — not patient data."


def _style() -> None:
    sns.set_theme(style="whitegrid", font_scale=1.05)
    plt.rcParams.update(
        {
            "figure.dpi": DPI,
            "savefig.dpi": DPI,
            "savefig.bbox": "tight",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def savefig(fig, stem: str) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    for ext in (".png", ".pdf", ".svg"):
        fig.savefig(FIG / f"{stem}{ext}")
    plt.close(fig)


def fig_architecture() -> None:
    fig, ax = plt.subplots(figsize=(9.2, 3.3))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 3.2)
    ax.axis("off")
    boxes = [
        (0.15, 1.0, "4-FSR insole\nMET1/2/5+HEEL"),
        (2.4, 1.0, "ESP32\n25 Hz ADC"),
        (4.5, 1.0, "BLE 28-byte\nXS packet"),
        (6.6, 1.0, "Features\nPPP/PTI/gait"),
        (8.7, 1.7, "ML risk\ncharacterization"),
        (8.7, 0.25, "Engineering\nalert threshold"),
        (10.5, 1.0, "Mobile\nrecord"),
    ]
    for x, y, t in boxes:
        ax.add_patch(plt.Rectangle((x, y), 1.7, 1.15, facecolor="#e8f1fb", edgecolor="#1f4e79", lw=1.3))
        ax.text(x + 0.85, y + 0.58, t, ha="center", va="center", fontsize=8)
    ax.set_title(f"X-Step system architecture\n{CAPTION_SYN}", loc="left")
    savefig(fig, "fig01_architecture")


def fig_plantar_layout() -> None:
    fig, ax = plt.subplots(figsize=(4.6, 6.2))
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-0.2, 3.2)
    ax.set_aspect("equal")
    ax.axis("off")
    theta = np.linspace(0, 2 * np.pi, 80)
    ax.plot(0.55 * np.sin(theta), 1.35 + 1.55 * np.cos(theta) * 0.55, "k-", lw=1.4)
    sites = {
        "MET1": (0.18, 2.35),
        "MET2": (0.0, 2.28),
        "MET5": (-0.28, 2.15),
        "HEEL": (0.0, 0.55),
    }
    for name, (x, y) in sites.items():
        ax.plot(x, y, "o", ms=14, color="#c0392b")
        ax.text(x + 0.38, y, name, va="center", fontsize=10)
    ax.set_title(f"Four-site plantar layout\n{CAPTION_SYN}")
    savefig(fig, "fig02_plantar_layout")


def fig_pipeline() -> None:
    fig_architecture()  # alias quality; dedicated pipeline graphic
    fig, ax = plt.subplots(figsize=(8.8, 2.8))
    ax.axis("off")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 2)
    steps = ["Raw ADC", "Calibrated kPa", "Window", "Features", "Model / threshold", "Alert + record"]
    for i, s in enumerate(steps):
        ax.add_patch(plt.Rectangle((0.2 + i * 1.6, 0.6), 1.4, 0.8, facecolor="#f7f3ea", edgecolor="#5c4a1f"))
        ax.text(0.9 + i * 1.6, 1.0, s, ha="center", va="center", fontsize=8)
        if i < len(steps) - 1:
            ax.annotate("", xy=(0.2 + (i + 1) * 1.6, 1.0), xytext=(1.6 + i * 1.6, 1.0), arrowprops=dict(arrowstyle="->"))
    ax.set_title(f"End-to-end data pipeline\n{CAPTION_SYN}")
    savefig(fig, "fig03_pipeline")


def fig_gait_cycle() -> None:
    rng = np.random.default_rng(0)
    frames, _, _ = synthesize_window("left_forefoot_overload", rng, seconds=2.0, hz=50.0, noise_std=1.0)
    t = np.arange(len(frames)) / 50.0
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    for i, site in enumerate(SensorSite):
        ax.plot(t, frames[:, i], label=f"L {SITE_LABELS[site]}")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Pressure (kPa)")
    ax.legend(fontsize=8)
    ax.set_title(f"Simulated left-foot traces (one overload pattern)\n{CAPTION_SYN}")
    savefig(fig, "fig04_gait_cycle")


def fig_from_results(data: dict) -> None:
    labels = data.get("per_model", {}).get("logreg", {}).get("labels")
    cm = data.get("per_model", {}).get("logreg", {}).get("confusion_matrix")
    if labels and cm:
        fig, ax = plt.subplots(figsize=(7.4, 6.4))
        sns.heatmap(
            np.asarray(cm),
            annot=True,
            fmt="d",
            cmap="Blues",
            xticklabels=[str(lab).replace("_", "\n") for lab in labels],
            yticklabels=[str(lab).replace("_", "\n") for lab in labels],
            ax=ax,
        )
        ax.set_xlabel("Predicted")
        ax.set_ylabel("True")
        ax.set_title(f"Grouped-CV confusion (logistic regression)\n{CAPTION_SYN}")
        savefig(fig, "fig06_confusion")

    baselines = data.get("baselines") or []
    if baselines:
        fig, ax = plt.subplots(figsize=(7.4, 4.2))
        names = [r["model"] for r in baselines]
        means = [r["macro_f1"] for r in baselines]
        lo = [r["macro_f1"] - r.get("macro_f1_ci95_lo", r["macro_f1"]) for r in baselines]
        hi = [r.get("macro_f1_ci95_hi", r["macro_f1"]) - r["macro_f1"] for r in baselines]
        ax.bar(names, means, yerr=[lo, hi], capsize=3)
        ax.set_ylim(0, 1.05)
        ax.set_ylabel("Macro-F1 (bootstrap 95% CI)")
        plt.xticks(rotation=25, ha="right")
        ax.set_title(f"Model comparison, subject-grouped CV\n{CAPTION_SYN}")
        savefig(fig, "fig07_model_comparison")

    sensor = data.get("sensor_ablation") or []
    if sensor:
        fig, ax = plt.subplots(figsize=(7.6, 4.2))
        ax.bar([r["subset"] for r in sensor], [r["macro_f1"] for r in sensor])
        ax.set_ylim(0, 1.05)
        plt.xticks(rotation=30, ha="right")
        ax.set_ylabel("Macro-F1")
        ax.set_title(f"Sensor-count ablation (logreg, grouped CV)\n{CAPTION_SYN}")
        savefig(fig, "fig08_sensor_ablation")

    robust = data.get("robustness") or []
    noise = [r for r in robust if r["perturbation"] == "gaussian_noise_kpa"]
    if noise:
        fig, ax = plt.subplots(figsize=(6.4, 3.8))
        ax.plot([r["severity"] for r in noise], [r["macro_f1"] for r in noise], marker="o")
        ax.set_xlabel("Gaussian noise SD (kPa)")
        ax.set_ylabel("Macro-F1 (held-out subjects)")
        ax.set_title(f"Robustness to sensor noise\n{CAPTION_SYN}")
        savefig(fig, "fig09_robustness_noise")

    drops = [r for r in robust if r["perturbation"] == "dropped_packets_frac"]
    if drops:
        fig, ax = plt.subplots(figsize=(6.4, 3.8))
        ax.plot([r["severity"] for r in drops], [r["macro_f1"] for r in drops], marker="o")
        ax.set_xlabel("Dropped-packet fraction")
        ax.set_ylabel("Macro-F1")
        ax.set_title(f"Robustness to BLE packet loss (simulated)\n{CAPTION_SYN}")
        savefig(fig, "fig10_packet_loss")

    lat = data.get("latency") or []
    measured = [r for r in lat if r.get("Mean Latency") not in ("", None)]
    if measured:
        fig, ax = plt.subplots(figsize=(7.4, 4.2))
        ax.barh([r["Stage"][:40] for r in measured], [float(r["Mean Latency"]) for r in measured])
        ax.set_xlabel("Mean latency (ms)")
        ax.set_title(f"Host pipeline timing (radio not measured)\n{CAPTION_SYN}")
        savefig(fig, "fig11_latency")

    # longitudinal simulated example
    rng = np.random.default_rng(3)
    days = np.arange(1, 15)
    pti = 80 + 4 * days + rng.normal(0, 3, size=len(days))
    fig, ax = plt.subplots(figsize=(6.6, 3.6))
    ax.plot(days, pti, marker="o")
    ax.set_xlabel("Session day (simulated)")
    ax.set_ylabel("MET2 PTI (kPa·s)")
    ax.set_title(f"Longitudinal pressure-load example (simulated)\n{CAPTION_SYN}")
    savefig(fig, "figS_longitudinal")

    fig, ax = plt.subplots(figsize=(5.5, 3.2))
    ax.text(
        0.5,
        0.5,
        "Ulcer photograph CNN omitted from the primary\nfour-site insole paper (unpaired public images).",
        ha="center",
        va="center",
    )
    ax.axis("off")
    ax.set_title("Supplementary: image model not in core paper")
    savefig(fig, "figS_ulcer_omitted")


def fig_from_csv() -> None:
    """Publication plots from frozen CSVs (does not retrain)."""
    import csv

    tab = _ROOT / "research" / "tables"
    ablation_path = tab / "sensor_ablation_publication.csv"
    if ablation_path.exists():
        with ablation_path.open() as f:
            rows = list(csv.DictReader(f))
        want = {
            "1_met2",
            "1_heel",
            "2_met1_met2",
            "2_met2_heel",
            "3_no_met1",
            "3_no_met5",
            "3_no_heel",
            "4_all",
        }
        rows = [r for r in rows if r.get("subset") in want]
        if rows:
            fig, ax = plt.subplots(figsize=(7.8, 4.3))
            labels = [
                r["Sensor Configuration"]
                .replace("3-site ", "")
                .replace("2-site ", "")
                .replace("1-site ", "")
                for r in rows
            ]
            y = [float(r["Performance"]) for r in rows]
            lo = [float(r["macro_f1_ci95_lo"]) for r in rows]
            hi = [float(r["macro_f1_ci95_hi"]) for r in rows]
            x = np.arange(len(rows))
            ax.bar(
                x,
                y,
                yerr=[np.array(y) - np.array(lo), np.array(hi) - np.array(y)],
                capsize=3,
                color="#1f4e79",
            )
            ax.set_xticks(x)
            ax.set_xticklabels(labels, rotation=28, ha="right", fontsize=8)
            ax.set_ylim(0, 1.05)
            ax.set_ylabel("Macro-F1 (subject-grouped CV)")
            ax.set_title(f"Sensor-site ablation (logistic regression)\n{CAPTION_SYN}")
            savefig(fig, "fig08_sensor_ablation")

    pkt = tab / "packet_loss_sweep.csv"
    if pkt.exists():
        with pkt.open() as f:
            rows = list(csv.DictReader(f))
        fig, ax = plt.subplots(figsize=(6.4, 3.8))
        ax.plot(
            [100 * float(r["severity"]) for r in rows],
            [float(r["macro_f1"]) for r in rows],
            marker="o",
            color="#1f4e79",
        )
        ax.set_xlabel("Simulated packet loss (%)")
        ax.set_ylabel("Macro-F1 (held-out subjects)")
        ax.set_title(f"Robustness to simulated packet loss\n{CAPTION_SYN}")
        savefig(fig, "fig10_packet_loss")

    models = tab / "model_comparison.csv"
    if models.exists():
        with models.open() as f:
            rows = list(csv.DictReader(f))
        fig, ax = plt.subplots(figsize=(7.4, 4.2))
        names = [r["model"] for r in rows]
        means = [float(r["macro_f1"]) for r in rows]
        lo = [float(r["macro_f1"]) - float(r["macro_f1_ci95_lo"]) for r in rows]
        hi = [float(r["macro_f1_ci95_hi"]) - float(r["macro_f1"]) for r in rows]
        ax.bar(names, means, yerr=[lo, hi], capsize=3, color="#1f4e79")
        ax.set_ylim(0, 1.05)
        ax.set_ylabel("Macro-F1 (bootstrap 95% CI)")
        plt.xticks(rotation=25, ha="right")
        ax.set_title(f"Model comparison, subject-grouped CV\n{CAPTION_SYN}")
        savefig(fig, "fig07_model_comparison")

    lat_path = _ROOT / "research" / "results" / "latency_host.json"
    if lat_path.exists():
        lat = json.loads(lat_path.read_text())
        fig, ax = plt.subplots(figsize=(7.0, 3.6))
        stages = ["Feature extraction", "Logistic regression", "Host path"]
        means = [lat["feature_mean_ms"], lat["logreg_mean_ms"], lat["host_path_mean_ms"]]
        p95 = [lat["feature_p95_ms"], lat["logreg_p95_ms"], lat["host_path_p95_ms"]]
        y = np.arange(len(stages))
        ax.barh(y, means, color="#1f4e79")
        ax.set_yticks(y)
        ax.set_yticklabels(stages)
        ax.set_xlabel("Mean latency (ms); whiskers = P95")
        ax.errorbar(
            means,
            y,
            xerr=[np.zeros(3), np.array(p95) - np.array(means)],
            fmt="none",
            ecolor="k",
            capsize=3,
        )
        ax.set_title(f"Host-side latency (BLE radio not measured)\n{CAPTION_SYN}")
        savefig(fig, "fig11_latency")

    summary = tab / "publication" / "table_V_robustness_summary.csv"
    if summary.exists():
        with summary.open() as f:
            rows = [r for r in csv.DictReader(f) if r.get("perturbation") != "none"]
        if rows:
            fig, ax = plt.subplots(figsize=(7.4, 4.0))
            labels = [r["perturbation"].replace("_", " ") for r in rows]
            y = [float(r["perturbed_macro_f1"]) for r in rows]
            base = float(rows[0]["baseline_macro_f1"]) if rows else 0.85
            ax.axhline(base, color="#888", ls="--", label=f"holdout baseline {base:.3f}")
            ax.bar(range(len(rows)), y, color="#8c2d04")
            ax.set_xticks(range(len(rows)))
            ax.set_xticklabels(labels, rotation=25, ha="right", fontsize=8)
            ax.set_ylim(0, 1.05)
            ax.set_ylabel("Macro-F1")
            ax.legend(frameon=False)
            ax.set_title(f"Robustness summary (held-out subjects)\n{CAPTION_SYN}")
            savefig(fig, "fig_robustness_summary")


def _alias_calibration() -> None:
    from shutil import copyfile

    if (FIG / "fig05_calibration.png").exists():
        return
    src = FIG / "fig_calibration_measured_vs_pred.png"
    if src.exists():
        for ext in (".png", ".pdf", ".svg"):
            s = FIG / f"fig_calibration_measured_vs_pred{ext}"
            d = FIG / f"fig05_calibration{ext}"
            if s.exists():
                copyfile(s, d)


def main() -> None:
    _style()
    fig_architecture()
    fig_plantar_layout()
    fig_pipeline()
    fig_gait_cycle()
    if RES.exists():
        data = json.loads(RES.read_text())
        fig_from_results(data)
    fig_from_csv()
    _alias_calibration()
    print(f"Wrote figures under {FIG}")


if __name__ == "__main__":
    main()
