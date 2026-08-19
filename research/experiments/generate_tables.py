#!/usr/bin/env python3
"""Copy/normalize publication tables. Primary CSVs are written by run_research.py."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
TAB = _ROOT / "research" / "tables"
RES = _ROOT / "research" / "results" / "research_results.json"
SYS = TAB / "system_performance.csv"


def main() -> None:
    src = TAB / "table6_system_performance.csv"
    if src.exists():
        shutil.copyfile(src, SYS)
    if not RES.exists():
        print("missing research/results/research_results.json — run make experiments", file=sys.stderr)
        sys.exit(1)
    data = json.loads(RES.read_text())
    print(f"tables ok; n_windows={data.get('n_windows')} data_source={data.get('data_source')}")


if __name__ == "__main__":
    main()
