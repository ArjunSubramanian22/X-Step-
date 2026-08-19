import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_research_configs_exist():
    for name in ("default.json", "smoke.json"):
        p = ROOT / "research" / "configs" / name
        assert p.is_file(), p
        json.loads(p.read_text())
