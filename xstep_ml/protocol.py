"""Binary BLE payload codec for X-Step insoles.

Packet (little-endian, 28 bytes):
  magic      2  b"XS"
  version    1  uint8
  flags      1  bit0=left, bit1=right, bit2=temp_present, bit3=charging
  seq        2  uint16
  t_ms       4  uint32 milliseconds since boot
  pressure   8  4 x uint16 ADC (MET1, MET2, MET5, HEEL)
  battery    1  uint8 percent
  reserved   1
  temp_c     8  4 x int16 tenths of a degree C (optional; zeros if absent)
"""

from __future__ import annotations

import struct
from dataclasses import dataclass

from xstep_ml.hardware import PROTOCOL_MAGIC, PROTOCOL_VERSION, SensorSite, adc_to_kpa

PACKET_STRUCT = struct.Struct("<2sBBHI4HBB4h")
PACKET_SIZE = PACKET_STRUCT.size  # 28


@dataclass
class InsolePacket:
    version: int
    side: str
    seq: int
    t_ms: int
    adc: tuple[int, int, int, int]
    kpa: tuple[float, float, float, float]
    battery: int
    charging: bool
    temperatures_c: tuple[float, float, float, float] | None

    def as_site_map(self) -> dict[str, float]:
        return {
            SensorSite.MET1.name.lower(): self.kpa[0],
            SensorSite.MET2.name.lower(): self.kpa[1],
            SensorSite.MET5.name.lower(): self.kpa[2],
            SensorSite.HEEL.name.lower(): self.kpa[3],
        }


def encode_packet(
    side: str,
    seq: int,
    t_ms: int,
    adc: tuple[int, int, int, int],
    battery: int,
    temperatures_c: tuple[float, float, float, float] | None = None,
    charging: bool = False,
    baseline_adc: tuple[int, int, int, int] = (0, 0, 0, 0),
) -> bytes:
    flags = 1 if side == "left" else 2
    if temperatures_c is not None:
        flags |= 4
    if charging:
        flags |= 8
    temps = temperatures_c or (0.0, 0.0, 0.0, 0.0)
    temp_i = tuple(int(round(t * 10)) for t in temps)
    return PACKET_STRUCT.pack(
        PROTOCOL_MAGIC,
        PROTOCOL_VERSION,
        flags,
        seq & 0xFFFF,
        t_ms & 0xFFFFFFFF,
        *(int(a) for a in adc),
        int(battery) & 0xFF,
        0,
        *temp_i,
    )


def decode_packet(
    raw: bytes,
    baseline_adc: tuple[int, int, int, int] = (0, 0, 0, 0),
) -> InsolePacket:
    if len(raw) < PACKET_SIZE:
        raise ValueError(f"short packet: {len(raw)} < {PACKET_SIZE}")
    magic, version, flags, seq, t_ms, a0, a1, a2, a3, battery, _res, t0, t1, t2, t3 = (
        PACKET_STRUCT.unpack(raw[:PACKET_SIZE])
    )
    if magic != PROTOCOL_MAGIC:
        raise ValueError(f"bad magic {magic!r}")
    side = "left" if flags & 1 else "right"
    adc = (a0, a1, a2, a3)
    kpa = tuple(adc_to_kpa(a, b) for a, b in zip(adc, baseline_adc))
    temps = None
    if flags & 4:
        temps = (t0 / 10.0, t1 / 10.0, t2 / 10.0, t3 / 10.0)
    return InsolePacket(
        version=version,
        side=side,
        seq=seq,
        t_ms=t_ms,
        adc=adc,
        kpa=kpa,  # type: ignore[arg-type]
        battery=battery,
        charging=bool(flags & 8),
        temperatures_c=temps,
    )
