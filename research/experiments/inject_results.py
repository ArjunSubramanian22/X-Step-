#!/usr/bin/env python3
"""Write research/manuscript/results_fragment.md from CSV/JSON (never hand-typed metrics)."""

from __future__ import annotations

import csv
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
TAB = _ROOT / "research" / "tables"
RES = _ROOT / "research" / "results" / "research_results.json"
OUT = _ROOT / "research" / "manuscript" / "results_fragment.md"


def _md(path: Path) -> str:
    if not path.exists():
        return f"_Missing {path.name}_\n"
    with path.open() as f:
        rows = list(csv.reader(f))
    if not rows:
        return f"_Empty {path.name}_\n"
    header, body = rows[0], rows[1:]
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join(["---"] * len(header)) + " |"]
    for row in body:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines) + "\n"


def main() -> None:
    meta = json.loads(RES.read_text()) if RES.exists() else {}
    parts = [
        f"**Data source:** `{meta.get('data_source', 'unknown')}`  ",
        f"**Validation type:** `{meta.get('validation_type', 'unknown')}`  ",
        f"**Windows / subjects:** {meta.get('n_windows', '?')} / {meta.get('n_subjects', '?')}  ",
        f"**Dataset hash:** `{meta.get('dataset_hash', '')[:16]}…`\n",
        "## Table 3. Model comparison (auto-generated)\n",
        _md(TAB / "table3_model_comparison.csv"),
        "## Table 4. Sensor ablation\n",
        _md(TAB / "table4_sensor_ablation.csv"),
        "## Table 5. Robustness (excerpt in CSV)\n",
        _md(TAB / "table5_robustness.csv"),
        "## Table 6. System performance\n",
        _md(TAB / "table6_system_performance.csv"),
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(parts))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
