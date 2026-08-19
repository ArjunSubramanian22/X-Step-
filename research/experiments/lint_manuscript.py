#!/usr/bin/env python3
"""Manuscript lint: placeholders, local paths, missing figures, terminology, registry numbers."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
MS = _ROOT / "research" / "manuscript" / "main.md"
REG = _ROOT / "research" / "results" / "final_results_registry.json"
TERM = _ROOT / "research" / "TERMINOLOGY.md"
FIG = _ROOT / "research" / "figures"
OUT = _ROOT / "research" / "results" / "manuscript_lint.json"

PLACEHOLDERS = [
    r"XXXXX",
    r"eXXXXX",
    r"TODO DOI",
    r"citation needed",
    r"\[INSERT",
    r"lorem ipsum",
    r"MANUAL VERIFICATION REQUIRED",  # allowed in checklist files, not in main.md
]
ABS_PATH = re.compile(r"/Users/[^\s)]+|C:\\Users\\")
BANNED_POSITIVE = [
    (r"\bclinically proven\b", "clinically proven"),
    (r"\bstate-of-the-art\b", "state-of-the-art"),
    (r"\bgroundbreaking\b", "groundbreaking"),
    (r"\brevolutionary\b", "revolutionary"),
    (r"\bunprecedented\b", "unprecedented"),
    (r"predicts ulcers", "predicts ulcers"),
    (r"detects ulcers", "detects ulcers"),
    (r"prevents amputations", "prevents amputations"),
]
APP_ZONES = re.compile(r"\b(toes|ball of foot|ball-of-foot)\b", re.I)
REQUIRED_FIGS = [
    "fig01_architecture.png",
    "fig02_plantar_layout.png",
    "fig03_pipeline.png",
    "fig04_gait_cycle.png",
    "fig06_confusion.png",
    "fig07_model_comparison.png",
    "fig08_sensor_ablation.png",
    "fig09_robustness_noise.png",
    "fig10_packet_loss.png",
    "fig11_latency.png",
]
REQUIRED_TOKENS = ["MET1", "MET2", "MET5", "HEEL", "synthetic", "GroupKFold"]


def _negated(line: str) -> bool:
    low = line.lower()
    return any(p in low for p in ("not ", "do not", "does not", "never ", "no ", "without "))


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    if not MS.exists():
        print("missing main.md", file=sys.stderr)
        return 2
    text = MS.read_text()
    for pat in PLACEHOLDERS:
        if re.search(pat, text, re.I):
            errors.append(f"placeholder {pat}")
    if ABS_PATH.search(text):
        errors.append("absolute local path in manuscript")
    for pat, name in BANNED_POSITIVE:
        for i, line in enumerate(text.splitlines(), 1):
            if re.search(pat, line, re.I) and not _negated(line):
                errors.append(f"{name} at line {i}")
    if APP_ZONES.search(text) and "APP_ZONE" not in text:
        # Allow a single terminology clarification paragraph.
        hits = [i for i, ln in enumerate(text.splitlines(), 1) if APP_ZONES.search(ln)]
        if len(hits) > 2:
            errors.append(f"non-canonical site names at lines {hits}")
    for tok in REQUIRED_TOKENS:
        if tok not in text:
            errors.append(f"missing required token {tok}")
    for fig in REQUIRED_FIGS:
        if not (FIG / fig).exists():
            errors.append(f"missing figure {fig}")
    # Duplicate figure labels like **Figure 1** twice with different content is OK;
    # duplicate markdown anchors are not checked here.
    labels = re.findall(r"\*\*Figure (\d+)\*\*", text)
    if labels and len(labels) != len(set(labels)):
        warnings.append(f"repeated Figure numbers: {labels}")
    if REG.exists():
        reg = json.loads(REG.read_text())
        must = [
            "logreg_grouped_macro_f1",
            "ablation_drop_met5_macro_f1",
            "packet_loss_30pct_macro_f1",
            "host_path_mean_ms",
        ]
        for key in must:
            rec = (reg.get("by_key") or {}).get(key) or {}
            disp = rec.get("display") or ""
            # Require the rounded three-decimal core, not the full CI string.
            core = disp.split("[")[0].strip().split(" ")[0]
            if core and core not in text and core.replace(" ms", "") not in text:
                warnings.append(f"registry display {key}={disp!r} not found in manuscript")
    if "Level A" not in text or "Level B" not in text or "Level C" not in text:
        errors.append("manuscript must distinguish evidence Level A/B/C")
    if "engineering risk-alert" not in text.lower() and "engineering risk-alert threshold" not in text.lower():
        warnings.append("missing engineering risk-alert threshold wording")
    payload = {"errors": errors, "warnings": warnings, "ok": not errors}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
