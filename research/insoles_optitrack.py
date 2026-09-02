"""32-cell insole + OptiTrack walking archive (not the X-Step four-site FSR).

The operator-provided zip matches the public InsolesOpitrackDataset layout
(Zenodo 10.5281/zenodo.20156243). Pressure channels are native 0–4096 counts
from a dense instrumented insole, not ESP32 FSR402 ADC mapped to kPa.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from scipy.signal import find_peaks

_ROOT = Path(__file__).resolve().parents[1]
LAYOUT_PATH = _ROOT / "research" / "data" / "insoles_optitrack" / "sensor_layout.json"
SITES = ("met1", "met2", "met5", "heel")
PRESSURE_PREFIX = "PressureSensor "
ASSUMED_INSOLE_HZ = 64.0  # sibling 32-channel MVP-GAIT schema (Zenodo 10.5281/zenodo.19662017)
EXCLUDE_PRESSURE = {("P13", "M1")}  # info.txt: insole desynchronization
EXCLUDE_MOCAP = {("P3", "M8"), ("P13", "M1")}
REPAIRED_MOCAP = {
    ("P3", "M5"): "M5.I",
    ("P3", "M6"): "M6.I",
    ("P13", "M8"): "M8.I",
    ("P13", "M9"): "M9.I",
    ("P15", "M3"): "M3.I",
}


def load_layout(path: Path = LAYOUT_PATH) -> dict:
    layout = json.loads(path.read_text())
    # Tests and left-foot defaults.
    if "regions" not in layout and "sides" in layout:
        layout["regions"] = layout["sides"]["left"]
    return layout


def regions_for_side(layout: dict, side: str) -> dict:
    sides = layout.get("sides") or {}
    key = "right" if str(side).lower().startswith("r") else "left"
    if key in sides:
        return sides[key]
    return layout["regions"]


def four_site_series(pressure: np.ndarray, layout: dict, side: str = "left") -> dict[str, np.ndarray]:
    regions = regions_for_side(layout, side)
    out = {}
    for site in SITES:
        i = int(regions[site]["representative"])
        out[site] = pressure[:, i]
    return out


def region_max_series(pressure: np.ndarray, layout: dict, side: str = "left") -> dict[str, np.ndarray]:
    regions = regions_for_side(layout, side)
    out = {}
    for site in SITES:
        members = [int(i) for i in regions[site]["members"]]
        out[site] = np.max(pressure[:, members], axis=1)
    return out


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _is_take_csv(name: str, suffix: str) -> bool:
    return name.endswith(suffix) and not name.startswith("__MACOSX")


def iter_take_keys(zf: zipfile.ZipFile) -> list[tuple[str, str]]:
    keys = set()
    for name in zf.namelist():
        if not _is_take_csv(name, "_Preassure_L.csv"):
            continue
        parts = Path(name).parts
        # InsolesOpitrackDataset/P1/M1/M1_Preassure_L.csv
        if len(parts) < 4:
            continue
        keys.add((parts[-3], parts[-2]))
    return sorted(keys, key=lambda x: (int(x[0][1:]), x[1].replace(".I", "").zfill(4), x[1]))


def unique_pressure_takes(keys: Iterable[tuple[str, str]]) -> list[tuple[str, str]]:
    """Prefer non-interpolated folders; .I is OptiTrack-only repair."""
    out = []
    for sid, take in keys:
        if take.endswith(".I"):
            continue
        out.append((sid, take))
    return out


def _read_csv_array(zf: zipfile.ZipFile, name: str) -> tuple[list[str], np.ndarray]:
    raw = zf.read(name).decode("utf-8", errors="replace")
    reader = csv.reader(io.StringIO(raw))
    header = next(reader)
    rows = [[float(x) if x != "" else np.nan for x in row] for row in reader if row]
    return header, np.asarray(rows, dtype=np.float64)


def pressure_csv_name(names: list[str], subject: str, take: str, side: str) -> str | None:
    tail = f"{subject}/{take}/{take}_Preassure_{side}.csv"
    for n in names:
        if n.endswith(tail) and not n.startswith("__MACOSX"):
            return n
    return None


def motion_csv_name(names: list[str], subject: str, take: str) -> str | None:
    use = REPAIRED_MOCAP.get((subject, take), take)
    tail = f"{subject}/{use}/{use}_Motion.csv"
    for n in names:
        if n.endswith(tail) and not n.startswith("__MACOSX"):
            return n
    return None


def load_pressure_side(zf: zipfile.ZipFile, name: str) -> dict[str, np.ndarray]:
    header, arr = _read_csv_array(zf, name)
    idx = {h: i for i, h in enumerate(header)}
    pcols = [idx[f"{PRESSURE_PREFIX}{i}"] for i in range(32)]
    pressure = arr[:, pcols]
    extra = {}
    for key in ("copX", "copY", "sumP"):
        if key in idx:
            extra[key] = arr[:, idx[key]]
    return {"pressure": pressure, **extra, "n": int(pressure.shape[0])}


def pearson(a: np.ndarray, b: np.ndarray) -> float:
    mask = np.isfinite(a) & np.isfinite(b)
    if mask.sum() < 8:
        return float("nan")
    aa, bb = a[mask], b[mask]
    if np.std(aa) < 1e-9 or np.std(bb) < 1e-9:
        return float("nan")
    return float(np.corrcoef(aa, bb)[0, 1])


def four_site_cop(four: dict[str, np.ndarray], layout: dict, side: str = "left") -> tuple[np.ndarray, np.ndarray]:
    xy = layout["representative_xy_unit_foot"]
    weights = np.stack([four[s] for s in SITES], axis=1)
    pos = np.array([xy[s] for s in SITES], dtype=np.float64)
    if str(side).lower().startswith("r"):
        pos = pos.copy()
        pos[:, 0] *= -1.0
    w = np.clip(weights, 0, None)
    denom = np.sum(w, axis=1, keepdims=True)
    denom = np.where(denom < 1e-6, np.nan, denom)
    cop = (w @ pos) / denom
    # Native copY in this archive is posterior-positive; unit-foot y is anterior-positive.
    return cop[:, 0], -cop[:, 1]


def heel_before_forefoot(four: dict[str, np.ndarray], mask: np.ndarray) -> bool:
    if mask.sum() < 5:
        return False
    ttp = {s: int(np.argmax(four[s][mask])) for s in SITES}
    met = float(np.mean([ttp["met1"], ttp["met2"], ttp["met5"]]))
    return ttp["heel"] < met


def contact_mask(sum_p: np.ndarray) -> np.ndarray:
    lo, hi = np.percentile(sum_p, [15, 90])
    thr = lo + 0.20 * max(hi - lo, 1.0)
    return sum_p > thr


def step_peaks(sum_p: np.ndarray, sample_hz: float) -> np.ndarray:
    dist = max(6, int(0.35 * sample_hz))
    height = np.percentile(sum_p, 55)
    peaks, _ = find_peaks(sum_p, height=height, distance=dist)
    return peaks


def icc_oneway(matrix: np.ndarray) -> float:
    """ICC(1,1) on subjects × repeated takes; NaNs dropped per row if incomplete."""
    x = np.asarray(matrix, dtype=np.float64)
    good = [row for row in x if np.isfinite(row).sum() >= 2]
    if len(good) < 3:
        return float("nan")
    k = min(int(np.isfinite(row).sum()) for row in good)
    rows = []
    for row in good:
        vals = row[np.isfinite(row)][:k]
        if len(vals) == k:
            rows.append(vals)
    y = np.vstack(rows)
    n, k = y.shape
    if n < 3 or k < 2:
        return float("nan")
    grand = y.mean()
    subject_means = y.mean(axis=1, keepdims=True)
    bms = k * np.sum((subject_means - grand) ** 2) / (n - 1)
    wms = np.sum((y - subject_means) ** 2) / (n * (k - 1))
    den = bms + (k - 1) * wms
    if den <= 0:
        return float("nan")
    return float((bms - wms) / den)


def mocap_path_length_m(zf: zipfile.ZipFile, name: str) -> tuple[float, int]:
    header, arr = _read_csv_array(zf, name)
    idx = {h: i for i, h in enumerate(header)}
    cols = [idx[c] for c in ("bone_Root_pos_x", "bone_Root_pos_y", "bone_Root_pos_z") if c in idx]
    if len(cols) != 3:
        return float("nan"), 0
    pos = arr[:, cols]
    finite = np.isfinite(pos).all(axis=1)
    pos = pos[finite]
    if len(pos) < 4:
        return float("nan"), int(arr.shape[0])
    step = np.linalg.norm(np.diff(pos, axis=0), axis=1)
    return float(np.nansum(step) / 1000.0), int(arr.shape[0])


def load_participants(zf: zipfile.ZipFile) -> dict[str, Any]:
    name = next(n for n in zf.namelist() if n.endswith("participants.csv") and not n.startswith("__MACOSX"))
    raw = zf.read(name).decode("utf-8")
    rows = list(csv.DictReader(io.StringIO(raw)))
    ages = [float(r["age"]) for r in rows]
    heights = [float(r["height_cm"]) for r in rows]
    weights = [float(r["weight_kg"]) for r in rows]
    sex = [r.get("sex") or r.get("gender") or "" for r in rows]
    return {
        "n": len(rows),
        "age_min": min(ages),
        "age_max": max(ages),
        "age_mean": float(np.mean(ages)),
        "height_cm_min": min(heights),
        "height_cm_max": max(heights),
        "weight_kg_min": min(weights),
        "weight_kg_max": max(weights),
        "n_female": sum(1 for s in sex if str(s).lower().startswith("f")),
        "n_male": sum(1 for s in sex if str(s).lower().startswith("m")),
        "subject_codes": [r["participant_code"] for r in rows],
    }


def evaluate_archive(zip_path: Path, *, insole_hz: float = ASSUMED_INSOLE_HZ) -> dict[str, Any]:
    layout = load_layout()
    zip_path = Path(zip_path)
    digest = sha256_file(zip_path)
    per_take: list[dict[str, Any]] = []
    heel_first = 0
    heel_first_n = 0
    peaks_by_subject: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))

    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        demo = load_participants(zf)
        keys = unique_pressure_takes(iter_take_keys(zf))
        n_folders = len(iter_take_keys(zf))
        for subject, take in keys:
            rec: dict[str, Any] = {
                "subject_id": subject,
                "take_id": take,
                "exclude_pressure": (subject, take) in EXCLUDE_PRESSURE,
                "exclude_mocap": (subject, take) in EXCLUDE_MOCAP,
            }
            if rec["exclude_pressure"]:
                rec["reason"] = "info.txt: insole desynchronization"
                per_take.append(rec)
                continue
            ln = pressure_csv_name(names, subject, take, "L")
            rn = pressure_csv_name(names, subject, take, "R")
            if not ln or not rn:
                rec["reason"] = "missing pressure csv"
                per_take.append(rec)
                continue
            left = load_pressure_side(zf, ln)
            right = load_pressure_side(zf, rn)
            rec["n_samples_left"] = left["n"]
            rec["n_samples_right"] = right["n"]
            rec["n_samples"] = int(min(left["n"], right["n"]))
            rec["pressure_min"] = float(min(left["pressure"].min(), right["pressure"].min()))
            rec["pressure_max"] = float(max(left["pressure"].max(), right["pressure"].max()))

            for side, blk in (("left", left), ("right", right)):
                four = four_site_series(blk["pressure"], layout, side)
                dense = region_max_series(blk["pressure"], layout, side)
                for site in SITES:
                    rec[f"{side}_{site}_sparse_peak"] = float(np.nanmax(four[site]))
                    rec[f"{side}_{site}_dense_peak"] = float(np.nanmax(dense[site]))
                    rec[f"{side}_{site}_peak_r"] = pearson(four[site], dense[site])
                if "copX" in blk and "copY" in blk:
                    cx, cy = four_site_cop(four, layout, side)
                    rec[f"{side}_copx_r"] = pearson(cx, blk["copX"])
                    rec[f"{side}_copy_r"] = pearson(cy, blk["copY"])
                if "sumP" in blk:
                    peaks = step_peaks(blk["sumP"], insole_hz)
                    rec[f"{side}_n_steps"] = int(len(peaks))
                    rec[f"{side}_sumP_peak"] = float(np.nanmax(blk["sumP"]))
                    mask = contact_mask(blk["sumP"])
                    rec[f"{side}_contact_frac"] = float(mask.mean())
                    heel_first_n += 1
                    if heel_before_forefoot(four, mask):
                        heel_first += 1
            # subject-level peaks (left foot, take-level)
            peaks_by_subject[subject]["sumP"].append(rec.get("left_sumP_peak", float("nan")))
            for site in SITES:
                peaks_by_subject[subject][site].append(rec.get(f"left_{site}_dense_peak", float("nan")))

            mn = motion_csv_name(names, subject, take)
            if mn and not rec["exclude_mocap"]:
                path_m, n_m = mocap_path_length_m(zf, mn)
                rec["n_motion_frames"] = n_m
                rec["root_path_m"] = path_m
                if n_m and rec["n_samples"]:
                    rec["motion_pressure_ratio"] = float(n_m / rec["n_samples"])
                    dur = rec["n_samples"] / insole_hz
                    rec["duration_s_assumed_64hz"] = float(dur)
                    rec["speed_m_s_assumed_64hz"] = float(path_m / dur) if dur > 0 else float("nan")
            per_take.append(rec)

    analyzed = [r for r in per_take if not r.get("exclude_pressure") and "n_samples" in r]
    ratios = [r["motion_pressure_ratio"] for r in analyzed if r.get("motion_pressure_ratio")]
    speeds = [r["speed_m_s_assumed_64hz"] for r in analyzed if np.isfinite(r.get("speed_m_s_assumed_64hz", np.nan))]

    def _median(key: str) -> float:
        vals = [r[key] for r in analyzed if np.isfinite(r.get(key, np.nan))]
        return float(np.median(vals)) if vals else float("nan")

    def _pool_r(prefix: str, site: str) -> float:
        vals = []
        for side in ("left", "right"):
            vals.extend(r[f"{side}_{site}_{prefix}"] for r in analyzed if f"{side}_{site}_{prefix}" in r)
        vals = [v for v in vals if np.isfinite(v)]
        return float(np.median(vals)) if vals else float("nan")

    region_rows = []
    for site in SITES:
        sparse, dense = [], []
        rs = []
        for r in analyzed:
            for side in ("left", "right"):
                s = r.get(f"{side}_{site}_sparse_peak")
                d = r.get(f"{side}_{site}_dense_peak")
                if s is None or d is None:
                    continue
                sparse.append(s)
                dense.append(d)
                rs.append(r.get(f"{side}_{site}_peak_r", float("nan")))
        sparse_a = np.asarray(sparse, dtype=float)
        dense_a = np.asarray(dense, dtype=float)
        peak_r = pearson(sparse_a, dense_a)
        rmse = float(np.sqrt(np.mean((sparse_a - dense_a) ** 2))) if len(sparse_a) else float("nan")
        nrmse = float(rmse / np.mean(dense_a)) if len(dense_a) and np.mean(dense_a) else float("nan")
        region_rows.append(
            {
                "site": site,
                "n_foot_takes": len(sparse_a),
                "median_timeseries_r": _pool_r("peak_r", site),
                "peak_peak_r": peak_r,
                "peak_rmse_counts": rmse,
                "peak_nrmse": nrmse,
                "median_sparse_peak": float(np.median(sparse_a)) if len(sparse_a) else float("nan"),
                "median_dense_peak": float(np.median(dense_a)) if len(dense_a) else float("nan"),
            }
        )

    copx = [r[k] for r in analyzed for k in ("left_copx_r", "right_copx_r") if np.isfinite(r.get(k, np.nan))]
    copy = [r[k] for r in analyzed for k in ("left_copy_r", "right_copy_r") if np.isfinite(r.get(k, np.nan))]

    subjects = sorted({r["subject_id"] for r in analyzed}, key=lambda s: int(s[1:]))
    icc = {}
    for feat in ("sumP", *SITES):
        mat = []
        for sid in subjects:
            mat.append(peaks_by_subject[sid].get(feat, []))
        # ragged -> pad
        width = max((len(x) for x in mat), default=0)
        m = np.full((len(mat), width), np.nan)
        for i, row in enumerate(mat):
            m[i, : len(row)] = row
        icc[feat] = icc_oneway(m)

    heel_first_frac = float(heel_first / heel_first_n) if heel_first_n else float("nan")

    n_steps = [r.get("left_n_steps", 0) + r.get("right_n_steps", 0) for r in analyzed]

    return {
        "task": "human_32site_optitrack_sparse_vs_dense",
        "data_source": "human",
        "hardware": "32-cell instrumented insole + OptiTrack Baseline Lower (not X-Step 4-FSR402)",
        "not_xstep_four_site_fsr": True,
        "source_zip": zip_path.name,
        "source_zip_sha256": digest,
        "zenodo_record": "10.5281/zenodo.20156243",
        "layout_file": str(LAYOUT_PATH.relative_to(_ROOT)),
        "assumed_insole_hz": insole_hz,
        "assumed_insole_hz_note": (
            "Pressure CSVs have no timestamps. 64 Hz is the nominal rate of a sibling "
            "public 32-channel insole schema from the same software stack "
            "(10.5281/zenodo.19662017). Seconds and m/s use this assumption."
        ),
        "n_take_folders": n_folders,
        "n_unique_pressure_takes": len(keys),
        "n_takes_analyzed": len(analyzed),
        "n_takes_excluded_pressure": sum(1 for r in per_take if r.get("exclude_pressure")),
        "n_subjects": len(subjects),
        "subject_ids": subjects,
        "demographics_aggregate": demo,
        "median_n_pressure_samples": _median("n_samples"),
        "median_motion_pressure_ratio": float(np.median(ratios)) if ratios else float("nan"),
        "median_speed_m_s_assumed_64hz": float(np.median(speeds)) if speeds else float("nan"),
        "median_duration_s_assumed_64hz": _median("duration_s_assumed_64hz"),
        "median_root_path_m": _median("root_path_m"),
        "median_steps_both_feet": float(np.median(n_steps)) if n_steps else float("nan"),
        "median_copx_r": float(np.median(copx)) if copx else float("nan"),
        "median_copy_r": float(np.median(copy)) if copy else float("nan"),
        "heel_before_forefoot_frac": heel_first_frac,
        "within_subject_icc": icc,
        "icc_note": (
            "ICC is across unlabeled M1–M10 takes, not repeated identical walking trials. "
            "Do not report as test–retest reliability."
        ),
        "per_region": region_rows,
        "exclusions": {
            "pressure": sorted(f"{a}/{b}" for a, b in EXCLUDE_PRESSURE),
            "mocap": sorted(f"{a}/{b}" for a, b in EXCLUDE_MOCAP),
            "mocap_repaired_used": {f"{a}/{b}": v for (a, b), v in REPAIRED_MOCAP.items()},
        },
        "ethics_note": "No IRB/ethics approval number is present in the zip. Do not invent one.",
        "takes": per_take,
    }


def evaluate_arrays(
    left: np.ndarray,
    right: np.ndarray,
    *,
    layout: dict | None = None,
    cop_left: tuple[np.ndarray, np.ndarray] | None = None,
) -> dict[str, Any]:
    """Fixture-friendly evaluation of two (T, 32) arrays."""
    layout = layout or load_layout()
    recs = []
    for side, arr in (("left", left), ("right", right)):
        four = four_site_series(arr, layout, side)
        dense = region_max_series(arr, layout, side)
        row = {"side": side}
        for site in SITES:
            row[f"{site}_sparse_peak"] = float(np.max(four[site]))
            row[f"{site}_dense_peak"] = float(np.max(dense[site]))
            row[f"{site}_r"] = pearson(four[site], dense[site])
        if cop_left and side == "left":
            cx, cy = four_site_cop(four, layout, "left")
            row["copx_r"] = pearson(cx, cop_left[0])
            row["copy_r"] = pearson(cy, cop_left[1])
        recs.append(row)
    return {"sides": recs, "not_xstep_four_site_fsr": True}
