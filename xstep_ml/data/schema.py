"""Canonical X-Step pressure-session schema.

Location names are identical in firmware, BLE, backend, ML, and the mobile
aliases (toes=met1, ball=met2, arch=met5, heel=heel).
"""

from __future__ import annotations

from typing import Any, Iterable, Literal, Sequence

import numpy as np
from pydantic import BaseModel, Field, field_validator

FootSide = Literal["left", "right"]
SensorLocation = Literal["met1", "met2", "met5", "heel"]
GaitPhase = Literal["unknown", "loading", "midstance", "propulsion", "swing"]
QualityFlag = Literal["ok", "noisy", "saturated", "missing", "packet_gap"]
DataSource = Literal["synthetic", "human", "bench", "simulated_example"]

CANONICAL_SITES: tuple[SensorLocation, ...] = ("met1", "met2", "met5", "heel")
SITE_INDEX = {name: i for i, name in enumerate(CANONICAL_SITES)}
CHANNEL_ORDER = tuple(f"L_{s}" for s in CANONICAL_SITES) + tuple(f"R_{s}" for s in CANONICAL_SITES)
APP_ZONE_ALIAS = {"toes": "met1", "ball": "met2", "arch": "met5", "heel": "heel"}
ADC_MAX = 4095


class PressureSample(BaseModel):
    """One calibrated sample at one plantar site."""

    subject_id: str
    session_id: str
    timestamp_ns: int
    foot_side: FootSide
    sensor_location: SensorLocation
    calibrated_pressure_kpa: float = Field(ge=0)
    raw_adc: int = Field(ge=0, le=ADC_MAX)
    sample_hz: float = Field(gt=0)
    stride_id: int | None = None
    gait_phase: GaitPhase = "unknown"
    sensor_quality: QualityFlag = "ok"
    packet_loss: bool = False
    calibration_version: str
    firmware_version: str
    data_source: DataSource = "synthetic"

    @field_validator("sensor_location")
    @classmethod
    def _site(cls, v: str) -> str:
        if v not in CANONICAL_SITES:
            raise ValueError(f"unknown site {v}; use {CANONICAL_SITES}")
        return v


class PressureFrame(BaseModel):
    """Eight-channel frame (left MET1/2/5/HEEL then right), kilopascals."""

    subject_id: str
    session_id: str
    timestamp_ns: int
    pressure_kpa: tuple[float, float, float, float, float, float, float, float]
    raw_adc: tuple[int, int, int, int, int, int, int, int] | None = None
    sample_hz: float = Field(gt=0)
    stride_id: int | None = None
    packet_loss: bool = False
    calibration_version: str
    firmware_version: str
    data_source: DataSource = "synthetic"

    @field_validator("pressure_kpa")
    @classmethod
    def _nonneg(cls, v: tuple[float, ...]) -> tuple[float, ...]:
        if any(x < 0 for x in v):
            raise ValueError("pressure_kpa must be >= 0")
        return v


class PressureWindowRecord(BaseModel):
    """ML observation: a contiguous window plus grouping identifiers."""

    subject_id: str
    session_id: str
    sample_hz: float = Field(gt=0)
    calibration_version: str
    firmware_version: str
    pressure_kpa: list[list[float]]
    raw_adc: list[list[int]] | None = None
    packet_loss_frac: float = Field(ge=0, le=1)
    gait_label: str | None = None
    zone_label: str | None = None
    data_source: DataSource = "synthetic"

    @field_validator("pressure_kpa")
    @classmethod
    def _shape(cls, v: list[list[float]]) -> list[list[float]]:
        if not v or any(len(row) != 8 for row in v):
            raise ValueError("pressure_kpa must be (T, 8)")
        arr = np.asarray(v, dtype=np.float64)
        if not np.isfinite(arr).all() or (arr < 0).any():
            raise ValueError("pressure_kpa must be finite and >= 0")
        return v


def normalize_location(name: str) -> SensorLocation:
    key = name.strip().lower().replace(" ", "_")
    key = APP_ZONE_ALIAS.get(key, key)
    aliases = {
        "1st_metatarsal": "met1",
        "first_metatarsal": "met1",
        "2nd_metatarsal": "met2",
        "second_metatarsal": "met2",
        "5th_metatarsal": "met5",
        "fifth_metatarsal": "met5",
        "calcaneus": "heel",
    }
    key = aliases.get(key, key)
    if key not in CANONICAL_SITES:
        raise ValueError(f"cannot map {name!r} to {CANONICAL_SITES}")
    return key  # type: ignore[return-value]


def validate_window_array(pressure_kpa: np.ndarray) -> np.ndarray:
    arr = np.asarray(pressure_kpa, dtype=np.float64)
    if arr.ndim != 2 or arr.shape[1] != 8:
        raise ValueError(f"expected (T, 8), got {arr.shape}")
    if not np.isfinite(arr).all():
        raise ValueError("non-finite pressure values")
    if (arr < 0).any():
        raise ValueError("negative pressure values")
    return arr


def validate_records(records: Iterable[PressureWindowRecord]) -> int:
    n = 0
    for rec in records:
        validate_window_array(np.asarray(rec.pressure_kpa, dtype=np.float64))
        n += 1
    if n == 0:
        raise ValueError("empty dataset")
    return n


def frames_to_samples(
    *,
    subject_id: str,
    session_id: str,
    frames_kpa: np.ndarray,
    sample_hz: float,
    calibration_version: str,
    firmware_version: str,
    data_source: DataSource = "synthetic",
    raw_adc: np.ndarray | None = None,
    t0_ns: int = 0,
) -> list[PressureSample]:
    arr = validate_window_array(frames_kpa)
    samples: list[PressureSample] = []
    dt_ns = int(round(1e9 / sample_hz))
    for t, row in enumerate(arr):
        ts = t0_ns + t * dt_ns
        for foot, offset in (("left", 0), ("right", 4)):
            for i, site in enumerate(CANONICAL_SITES):
                adc = 0
                if raw_adc is not None:
                    adc = int(raw_adc[t, offset + i])
                samples.append(
                    PressureSample(
                        subject_id=subject_id,
                        session_id=session_id,
                        timestamp_ns=ts,
                        foot_side=foot,  # type: ignore[arg-type]
                        sensor_location=site,
                        calibrated_pressure_kpa=float(row[offset + i]),
                        raw_adc=adc,
                        sample_hz=sample_hz,
                        calibration_version=calibration_version,
                        firmware_version=firmware_version,
                        data_source=data_source,
                    )
                )
    return samples


def assert_channel_names(names: Sequence[str]) -> None:
    if tuple(names) != CHANNEL_ORDER:
        raise ValueError(f"channel order must be {CHANNEL_ORDER}, got {tuple(names)}")


def dataset_hash(X: np.ndarray, y: np.ndarray, groups: np.ndarray) -> str:
    import hashlib

    h = hashlib.sha256()
    h.update(np.ascontiguousarray(X, dtype=np.float64).tobytes())
    h.update(np.asarray(y).astype("U").tobytes())
    h.update(np.ascontiguousarray(groups).tobytes())
    return h.hexdigest()


def json_ready(obj: Any) -> Any:
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.floating, np.integer)):
        return obj.item()
    if isinstance(obj, dict):
        return {str(k): json_ready(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [json_ready(v) for v in obj]
    return obj
