#!/usr/bin/env python3
"""Build the EHB submission package without retraining models.

Steps: validate registry, verify references, regenerate rounded tables/prose,
optionally regenerate figures, lint manuscript, copy dist/ehb26/, compile PDF if possible.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _run(args: list[str], *, cwd: Path | None = None) -> None:
    print("+", " ".join(args))
    subprocess.check_call(args, cwd=cwd or _ROOT)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _try_compile() -> Path | None:
    tex = _ROOT / "research" / "manuscript" / "main.tex"
    out_dir = _ROOT / "dist" / "ehb26" / "paper"
    out_dir.mkdir(parents=True, exist_ok=True)
    pdflatex = shutil.which("pdflatex")
    if not pdflatex:
        (out_dir / "COMPILE_STATUS.txt").write_text(
            "pdflatex not found. Canonical manuscript is research/manuscript/main.md.\n"
            "Camera-ready Word/Springer template remains HUMAN_VERIFICATION.\n"
        )
        return None
    try:
        subprocess.check_call(
            [pdflatex, "-interaction=nonstopmode", "-output-directory", str(out_dir), str(tex)],
            cwd=_ROOT / "research" / "manuscript",
        )
    except subprocess.CalledProcessError:
        (out_dir / "COMPILE_STATUS.txt").write_text(
            "pdflatex ran but failed (likely missing llncs.cls). Markdown remains canonical.\n"
        )
        return None
    pdf = out_dir / "main.pdf"
    return pdf if pdf.exists() else None


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--skip-figures", action="store_true")
    p.add_argument("--skip-lint", action="store_true")
    args = p.parse_args()

    _run([sys.executable, "research/experiments/build_registry.py"])
    _run([sys.executable, "research/experiments/generate_results.py"])
    _run([sys.executable, "research/experiments/inject_results.py"])
    _run([sys.executable, "research/experiments/verify_references.py"])
    _run([sys.executable, "research/experiments/scan_claims.py"])
    if not args.skip_figures:
        _run([sys.executable, "research/experiments/generate_figures.py"])
    if not args.skip_lint:
        _run([sys.executable, "research/experiments/lint_manuscript.py"])

    dist = _ROOT / "dist" / "ehb26"
    paper = dist / "paper"
    supp = dist / "supplement"
    repro = dist / "reproducibility"
    for d in (paper, supp, repro):
        d.mkdir(parents=True, exist_ok=True)

    for src in (
        "research/manuscript/main.md",
        "research/manuscript/main.tex",
        "research/manuscript/generated_results.md",
        "research/manuscript/FIGURE_CAPTIONS.md",
        "research/manuscript/EVIDENCE_GRAPH.md",
        "research/manuscript/REFERENCE_VERIFICATION_REPORT.md",
    ):
        path = _ROOT / src
        if path.exists():
            shutil.copy2(path, paper / path.name)

    fig_src = _ROOT / "research" / "figures"
    fig_dst = paper / "figures"
    if fig_src.exists():
        fig_dst.mkdir(exist_ok=True)
        for name in (
            "fig01_architecture",
            "fig02_plantar_layout",
            "fig03_pipeline",
            "fig04_gait_cycle",
            "fig06_confusion",
            "fig07_model_comparison",
            "fig08_sensor_ablation",
            "fig09_robustness_noise",
            "fig10_packet_loss",
            "fig11_latency",
        ):
            for ext in (".png", ".pdf", ".svg"):
                f = fig_src / f"{name}{ext}"
                if f.exists():
                    shutil.copy2(f, fig_dst / f.name)

    pub = _ROOT / "research" / "tables" / "publication"
    tab_dst = paper / "tables"
    tab_dst.mkdir(exist_ok=True)
    if pub.exists():
        for f in pub.glob("*.csv"):
            shutil.copy2(f, tab_dst / f.name)
    rel = _ROOT / "research" / "tables" / "related_systems.csv"
    if rel.exists():
        shutil.copy2(rel, tab_dst / rel.name)

    for src in (
        "research/supplement/README.md",
        "research/supplement/REPRODUCIBILITY_APPENDIX.md",
        "research/manuscript/SUPPLEMENTARY_ULCER.md",
        "research/configs/HYPERPARAMETERS.md",
        "research/METHODS_FEATURES.md",
        "research/tables/sensor_ablation_publication.csv",
        "research/tables/table5_robustness.csv",
        "research/tables/packet_loss_sweep.csv",
    ):
        path = _ROOT / src
        if path.exists():
            shutil.copy2(path, supp / path.name)

    for src in (
        "REPRODUCIBILITY.md",
        "research/results/final_results_registry.json",
        "research/results/manifest.json",
        "research/releases/EHB26_EXPERIMENTAL_FREEZE.md",
        "research/RED_TEAM_REPRODUCIBILITY.md",
    ):
        path = _ROOT / src
        if path.exists():
            shutil.copy2(path, repro / path.name)

    hashes = {}
    for path in [
        _ROOT / "research" / "manuscript" / "main.md",
        _ROOT / "research" / "results" / "final_results_registry.json",
        _ROOT / "research" / "tables" / "model_comparison.csv",
        _ROOT / "research" / "tables" / "sensor_ablation_publication.csv",
        _ROOT / "research" / "tables" / "packet_loss_sweep.csv",
    ]:
        if path.exists():
            hashes[str(path.relative_to(_ROOT))] = _sha256(path)
    (dist / "ARTIFACT_HASHES.json").write_text(json.dumps(hashes, indent=2) + "\n")
    (dist / "README.md").write_text(
        "\n".join(
            [
                "# EHB 2026 submission bundle",
                "",
                "This directory contains review artifacts only: manuscript source, figures, tables, supplement, reproducibility files.",
                "It does **not** contain private health data, secrets, or model-training outputs beyond frozen public tables.",
                "",
                "Canonical paper: `paper/main.md`.",
                "Do not retrain models as part of `make paper`.",
                "",
            ]
        )
    )

    pdf = _try_compile()
    status = {
        "retrained": False,
        "pdf": str(pdf) if pdf else None,
        "hashes": hashes,
    }
    print(json.dumps(status, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
