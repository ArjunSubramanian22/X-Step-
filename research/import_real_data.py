"""Import drop-in X-Step recordings into the canonical schema.

Usage (repo root):

    python -m research.import_real_data

Raw files under data/raw/ are never modified. Each successful run writes a new
directory data/processed/<run_id>/ and refuses to overwrite it.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from xstep_ml.data.schema import (  # noqa: E402
    CANONICAL_SITES,
    PressureWindowRecord,
    validate_records,
    validate_window_array,
)
from xstep_ml.hardware import (  # noqa: E402
    ADC_FULL_SCALE,
    CALIBRATION_VERSION,
    FIRMWARE_VERSION,
    HARDWARE_REVISION,
    adc_to_kpa,
)
from xstep_ml.protocol import PACKET_SIZE, decode_packet  # noqa: E402

RAW_DIR = _ROOT / "data" / "raw"
PROC_DIR = _ROOT / "data" / "processed"
ANON_SALT = "xstep-ehb26-anon-v1"
ADC_COLS = [f"{s}_adc" for s in CANONICAL_SITES]
KPA_COLS = [f"{s}_kpa" for s in CANONICAL_SITES]


def _rel(folder: Path) -> str:
    try:
        return str(folder.resolve().relative_to(_ROOT))
    except ValueError:
        return str(folder)


def anonymize_subject(raw_id: str) -> str:
    digest = hashlib.sha256(f"{ANON_SALT}|{raw_id.strip()}".encode()).hexdigest()[:10]
    return f"S{digest}"


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def _load_session_meta(folder: Path) -> dict:
    meta_path = folder / "session.json"
    if meta_path.is_file():
        return json.loads(meta_path.read_text())
    return {
        "subject_id": folder.name,
        "session_id": folder.name,
        "foot_side": "both",
        "footwear": "unspecified",
        "hardware_revision": HARDWARE_REVISION,
        "firmware_version": FIRMWARE_VERSION,
        "calibration_version": CALIBRATION_VERSION,
        "sample_hz": 25.0,
        "notes": "session.json missing; folder name used as ids",
    }


def _flag_adc(adc: int) -> str:
    if adc <= 0:
        return "missing"
    if adc >= int(ADC_FULL_SCALE):
        return "saturated"
    return "ok"


def _parse_csv(path: Path) -> list[dict]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def _rows_to_frames(rows: list[dict], sample_hz: float) -> tuple[np.ndarray, np.ndarray, list[str], int]:
    """Return pressure (T,4), adc (T,4), quality flags, n_seq_gaps for one foot."""
    if not rows:
        raise ValueError("empty traces")
    adc = np.zeros((len(rows), 4), dtype=np.int32)
    kpa = np.zeros((len(rows), 4), dtype=np.float64)
    flags: list[str] = []
    seqs = []
    have_kpa = all(c in rows[0] for c in KPA_COLS)
    for i, row in enumerate(rows):
        if "seq" in row and str(row["seq"]).strip() != "":
            seqs.append(int(float(row["seq"])))
        qualities = []
        for j, site in enumerate(CANONICAL_SITES):
            a = int(float(row[f"{site}_adc"]))
            adc[i, j] = a
            qualities.append(_flag_adc(a))
            if have_kpa and row.get(f"{site}_kpa") not in (None, ""):
                kpa[i, j] = float(row[f"{site}_kpa"])
            else:
                kpa[i, j] = adc_to_kpa(a)
        flags.append("ok" if all(q == "ok" for q in qualities) else ",".join(qualities))
    gaps = 0
    if seqs:
        diffs = np.diff(np.asarray(seqs, dtype=np.int64))
        gaps = int(np.sum(diffs > 1))
    if not np.isfinite(kpa).all() or (kpa < 0).any():
        raise ValueError("non-finite or negative kPa in traces")
    _ = sample_hz
    return kpa, adc, flags, gaps


def _parse_ble_bin(path: Path) -> list[dict]:
    raw = path.read_bytes()
    rows = []
    n = len(raw) // PACKET_SIZE
    for i in range(n):
        chunk = raw[i * PACKET_SIZE : (i + 1) * PACKET_SIZE]
        try:
            pkt = decode_packet(chunk)
        except Exception:
            continue
        row = {
            "timestamp_ns": int(pkt.t_ms) * 1_000_000,
            "seq": int(pkt.seq),
            "foot_side": pkt.side,
        }
        for site, a, p in zip(CANONICAL_SITES, pkt.adc, pkt.kpa):
            row[f"{site}_adc"] = int(a)
            row[f"{site}_kpa"] = float(p)
        rows.append(row)
    return rows


def _windows_from_json(path: Path, subject_id: str, session_id: str, meta: dict) -> list[PressureWindowRecord]:
    payload = json.loads(path.read_text())
    recs = []
    for item in payload:
        rec = PressureWindowRecord(
            subject_id=subject_id,
            session_id=item.get("session_id", session_id),
            sample_hz=float(item.get("sample_hz", meta.get("sample_hz", 25))),
            calibration_version=str(item.get("calibration_version", meta.get("calibration_version", CALIBRATION_VERSION))),
            firmware_version=str(item.get("firmware_version", meta.get("firmware_version", FIRMWARE_VERSION))),
            pressure_kpa=item["pressure_kpa"],
            raw_adc=item.get("raw_adc"),
            packet_loss_frac=float(item.get("packet_loss_frac", 0.0)),
            gait_label=item.get("gait_label"),
            zone_label=item.get("zone_label"),
            data_source="human",
        )
        recs.append(rec)
    return recs


def _align_bilateral(
    left: tuple[np.ndarray, np.ndarray] | None,
    right: tuple[np.ndarray, np.ndarray] | None,
) -> tuple[np.ndarray, np.ndarray]:
    """Stack left[T,4] + right[T,4] → (T,8). Missing side is zeros and flagged upstream."""
    if left is None and right is None:
        raise ValueError("no traces")
    t = (left[0] if left else right[0]).shape[0]
    kpa = np.zeros((t, 8), dtype=np.float64)
    adc = np.zeros((t, 8), dtype=np.int32)
    if left is not None:
        n = min(t, left[0].shape[0])
        kpa[:n, 0:4] = left[0][:n]
        adc[:n, 0:4] = left[1][:n]
    if right is not None:
        n = min(t, right[0].shape[0])
        kpa[:n, 4:8] = right[0][:n]
        adc[:n, 4:8] = right[1][:n]
    return kpa, adc


def import_session_folder(folder: Path) -> dict:
    meta = _load_session_meta(folder)
    raw_sid = str(meta.get("subject_id") or folder.name)
    subject_id = anonymize_subject(raw_sid)
    session_id = str(meta.get("session_id") or folder.name)
    hz = float(meta.get("sample_hz") or 25.0)
    cal = str(meta.get("calibration_version") or CALIBRATION_VERSION)
    fw = str(meta.get("firmware_version") or FIRMWARE_VERSION)

    windows_path = folder / "windows.json"
    if windows_path.is_file():
        recs = _windows_from_json(windows_path, subject_id, session_id, meta)
        validate_records(recs)
        return {
            "subject_id": subject_id,
            "session_id": session_id,
            "n_windows": len(recs),
            "records": [r.model_dump() for r in recs],
            "packet_gaps": 0,
            "metadata": {**meta, "hardware_revision": meta.get("hardware_revision", HARDWARE_REVISION)},
            "source_folder": _rel(folder),
        }

    left_rows: list[dict] = []
    right_rows: list[dict] = []
    for name in ("traces.csv", "traces_left.csv", "traces_right.csv"):
        p = folder / name
        if not p.is_file():
            continue
        rows = _parse_csv(p)
        if name == "traces_right.csv":
            right_rows.extend(rows)
            continue
        if name == "traces_left.csv":
            left_rows.extend(rows)
            continue
        for row in rows:
            side = str(row.get("foot_side", "left")).lower()
            if side == "right":
                right_rows.append(row)
            else:
                left_rows.append(row)

    ble = folder / "packets.ble.bin"
    if ble.is_file():
        for row in _parse_ble_bin(ble):
            if row.get("foot_side") == "right":
                right_rows.append(row)
            else:
                left_rows.append(row)

    if not left_rows and not right_rows:
        raise FileNotFoundError(f"no traces in {folder}")

    def _foot(rows: list[dict]) -> tuple[np.ndarray, np.ndarray, int] | None:
        if not rows:
            return None
        kpa, adc, _flags, gaps = _rows_to_frames(rows, hz)
        return kpa, adc, gaps

    lf = _foot(left_rows)
    rf = _foot(right_rows)
    left_pair = (lf[0], lf[1]) if lf else None
    right_pair = (rf[0], rf[1]) if rf else None
    frames, adc = _align_bilateral(left_pair, right_pair)
    validate_window_array(frames)
    gaps = (lf[2] if lf else 0) + (rf[2] if rf else 0)
    loss_frac = float(gaps / max(frames.shape[0], 1))
    rec = PressureWindowRecord(
        subject_id=subject_id,
        session_id=session_id,
        sample_hz=hz,
        calibration_version=cal,
        firmware_version=fw,
        pressure_kpa=frames.tolist(),
        raw_adc=adc.tolist(),
        packet_loss_frac=min(loss_frac, 1.0),
        data_source="human",
    )
    validate_records([rec])
    return {
        "subject_id": subject_id,
        "session_id": session_id,
        "n_windows": 1,
        "n_samples": int(frames.shape[0]),
        "packet_gaps": gaps,
        "invalid_sensor_frac": float(np.mean((adc <= 0) | (adc >= int(ADC_FULL_SCALE)))),
        "records": [rec.model_dump()],
        "metadata": {
            **meta,
            "anonymized_subject_id": subject_id,
            "hardware_revision": meta.get("hardware_revision", HARDWARE_REVISION),
            "footwear": meta.get("footwear", "unspecified"),
            "notes": meta.get("notes", ""),
        },
        "source_folder": _rel(folder),
    }


def discover_session_folders(raw_dir: Path = RAW_DIR) -> list[Path]:
    if not raw_dir.is_dir():
        return []
    out = []
    for child in sorted(raw_dir.iterdir()):
        if not child.is_dir() or child.name.startswith("."):
            continue
        markers = (
            "session.json",
            "traces.csv",
            "traces_left.csv",
            "traces_right.csv",
            "windows.json",
            "packets.ble.bin",
        )
        if any((child / m).exists() for m in markers):
            out.append(child)
    return out


def import_raw(raw_dir: Path = RAW_DIR, proc_dir: Path = PROC_DIR) -> dict:
    """Validate and write an immutable processed snapshot."""
    folders = discover_session_folders(raw_dir)
    run_id = _run_id()
    dest = proc_dir / run_id
    if dest.exists():
        raise FileExistsError(f"refusing to overwrite {dest}")
    sessions = []
    errors = []
    for folder in folders:
        try:
            sessions.append(import_session_folder(folder))
        except Exception as exc:
            errors.append({"folder": str(folder), "error": str(exc)})
    dest.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_id": run_id,
        "n_sessions_found": len(folders),
        "n_sessions_imported": len(sessions),
        "n_subjects": len({s["subject_id"] for s in sessions}),
        "data_source": "human" if sessions else "none",
        "raw_dir": str(raw_dir),
        "raw_unmodified": True,
        "sessions": [{k: v for k, v in s.items() if k != "records"} for s in sessions],
        "errors": errors,
    }
    (dest / "import_manifest.json").write_text(json.dumps(payload, indent=2, default=str))
    if sessions:
        records = []
        for s in sessions:
            records.extend(s["records"])
        (dest / "windows.json").write_text(json.dumps(records, indent=2))
    readme = dest / "README.md"
    readme.write_text(
        f"# Processed run `{run_id}`\n\n"
        f"Imported {payload['n_sessions_imported']} session(s) from `{raw_dir}`.\n"
        "This directory is immutable. Re-import writes a new run_id.\n"
    )
    return payload


def main() -> int:
    payload = import_raw()
    print(json.dumps({k: payload[k] for k in ("run_id", "n_sessions_found", "n_sessions_imported", "n_subjects", "errors")}, indent=2))
    if payload["n_sessions_imported"] == 0:
        print("No raw walking sessions found under data/raw/. Drop recordings there and re-run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
