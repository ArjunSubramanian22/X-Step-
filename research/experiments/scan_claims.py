#!/usr/bin/env python3
"""Flag risky clinical/marketing language in manuscript sources."""

from __future__ import annotations

import csv
import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
PATTERNS = [
    r"\bproves\b",
    r"\bguarantees\b",
    r"\bprevents\b",
    r"clinically validated",
    r"\bdiagnosis\b",
    r"predicts ulcers",
    r"\beliminates\b",
    r"\bsuperior\b",
    r"significantly better",
    r"\bFDA\b",
    r"amputation",
]
FILES = [
    _ROOT / "research" / "manuscript" / "main.md",
    _ROOT / "research" / "manuscript" / "main.tex",
    _ROOT / "research" / "manuscript" / "generated_results.md",
    _ROOT / "papers" / "ehb2026" / "manuscript_blind.md",
]


def main() -> None:
    rows = []
    rx = re.compile("|".join(PATTERNS), re.I)
    for path in FILES:
        if not path.exists():
            continue
        for i, line in enumerate(path.read_text().splitlines(), 1):
            if rx.search(line):
                rows.append({"file": str(path.relative_to(_ROOT)), "line": i, "text": line.strip()[:240]})
    out = _ROOT / "research" / "results" / "risky_language.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["file", "line", "text"])
        w.writeheader()
        w.writerows(rows)
    print(f"flagged {len(rows)} lines -> {out}")


if __name__ == "__main__":
    main()
