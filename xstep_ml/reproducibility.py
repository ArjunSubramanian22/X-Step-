"""Environment and experiment manifest helpers."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from xstep_ml import __version__
from xstep_ml.config import ROOT
from xstep_ml.data.schema import dataset_hash, json_ready


def git_sha(repo: Path | None = None) -> str:
    repo = repo or ROOT
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, stderr=subprocess.DEVNULL)
            .decode()
            .strip()
        )
    except Exception:
        return "unknown"


def python_packages() -> dict[str, str]:
    names = ("numpy", "scipy", "pandas", "sklearn", "matplotlib", "seaborn", "joblib", "pydantic", "fastapi", "pytest")
    out: dict[str, str] = {}
    for n in names:
        try:
            mod = __import__("sklearn" if n == "sklearn" else n)
            out[n] = getattr(mod, "__version__", "unknown")
        except Exception:
            out[n] = "missing"
    return out


def environment_record() -> dict[str, Any]:
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "machine": platform.machine(),
        "git_sha": git_sha(),
        "xstep_ml": __version__,
        "packages": python_packages(),
        "cwd": str(Path.cwd()),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "research_smoke": os.environ.get("RESEARCH_SMOKE", "0"),
    }


def write_manifest(path: Path, extra: dict[str, Any]) -> dict[str, Any]:
    payload = {"environment": environment_record(), **json_ready(extra)}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str))
    return payload


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def cohort_hash(X, y, groups) -> str:
    return dataset_hash(X, y, groups)
