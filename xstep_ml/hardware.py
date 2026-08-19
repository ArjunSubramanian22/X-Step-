"""X-Step smart insole hardware contract.

Each insole has four force-sensitive resistors at clinically high-risk plantar
sites (1st metatarsal, 2nd metatarsal, 5th metatarsal, heel) plus a BLE
microcontroller. Two insoles stream independently and are fused on the phone
or API into an eight-channel plantar frame.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

PROTOCOL_MAGIC = b"XS"
PROTOCOL_VERSION = 1
FIRMWARE_VERSION = "insole-protocol-v1"
HARDWARE_REVISION = "esp32-dev-fsr402-4ch"
FEATURE_EXTRACTOR_VERSION = "biomechanics-v59"
CALIBRATION_VERSION = "linear_adc_engineering_v0"
DEFAULT_SAMPLE_HZ = 25
GATT_SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
GATT_TX_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"
GATT_RX_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
DEVICE_NAME_PREFIX = "XSTEP"


class SensorSite(IntEnum):
    """Hardware channel order packed by firmware (left then right)."""

    MET1 = 0  # 1st metatarsal head — hallux/medial forefoot
    MET2 = 1  # 2nd metatarsal head — central forefoot
    MET5 = 2  # 5th metatarsal head — lateral column
    HEEL = 3  # calcaneus


SITE_LABELS = {
    SensorSite.MET1: "1st metatarsal",
    SensorSite.MET2: "2nd metatarsal",
    SensorSite.MET5: "5th metatarsal",
    SensorSite.HEEL: "heel",
}

# Map the original app zones onto the four FSR sites so UI stays compatible.
APP_ZONE_TO_SITE = {
    "toes": SensorSite.MET1,
    "ball": SensorSite.MET2,
    "arch": SensorSite.MET5,
    "heel": SensorSite.HEEL,
}

SITE_TO_APP_ZONE = {v: k for k, v in APP_ZONE_TO_SITE.items()}

# ADC (12-bit) to kilopascals. Engineering default, not a fitted bench curve.
# See xstep_ml.calibration for the research ADC→R→force pipeline.
ADC_FULL_SCALE = 4095.0
KPA_FULL_SCALE = 250.0  # literature DFU risk often cited near 200 kPa peak

# Peak plantar pressure thresholds used for alerts (kPa).
ALERT_PRESSURE_KPA = 75.0
HIGH_RISK_PEAK_KPA = 200.0
TEMP_ASYMMETRY_C = 2.2  # Lavery / Armstrong thermal asymmetry guideline


@dataclass(frozen=True)
class InsoleIdentity:
    side: str  # "left" | "right"
    firmware: str
    serial: str


def adc_to_kpa(adc: int, baseline_adc: int = 0) -> float:
    """Convert a raw ADC sample to kilopascals after subtracting unloaded baseline."""
    corrected = max(0, int(adc) - int(baseline_adc))
    return (corrected / ADC_FULL_SCALE) * KPA_FULL_SCALE


def kpa_to_adc(kpa: float) -> int:
    return int(max(0, min(ADC_FULL_SCALE, (kpa / KPA_FULL_SCALE) * ADC_FULL_SCALE)))
