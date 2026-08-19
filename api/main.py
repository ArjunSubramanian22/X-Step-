"""X-Step production inference API."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from xstep_ml.hardware import ALERT_PRESSURE_KPA, DEFAULT_SAMPLE_HZ, DEVICE_NAME_PREFIX, GATT_SERVICE_UUID
from xstep_ml.inference.engine import ProductionEngine, latest_frame_to_app_zones
from xstep_ml.inference.recommendations import build_recommendations, stepmate_system_prompt
from xstep_ml.inference.ulcer import UlcerImagePredictor
from xstep_ml.models.clinical import ClinicalProfile
from xstep_ml.protocol import decode_packet, encode_packet

app = FastAPI(
    title="X-Step ML API",
    version="1.0.0",
    description="Production inference for smart-insole pressure, gait, ulcer imaging, and care guidance.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_engine = ProductionEngine()
_ulcer = UlcerImagePredictor()


class ClinicalIn(BaseModel):
    diabetes_duration_years: float = 0
    hba1c: float = 7.0
    neuropathy: str = "None"
    prior_ulcer: bool = False
    amputation: bool = False
    vascular: bool = False
    smoking: str = "Never"
    age: float = 50
    work_type: str = "Sedentary"


class AnalyzeIn(BaseModel):
    frames: list[list[float]] = Field(..., description="(T, 8) kPa: L-met1,2,5,heel + R-met1,2,5,heel")
    sample_hz: float = DEFAULT_SAMPLE_HZ
    pressure_threshold: float = ALERT_PRESSURE_KPA
    temperatures: list[list[float]] | None = None
    compliance: float = 80
    clinical: ClinicalIn | None = None
    ulcer_grade: int | None = None
    ulcer_confidence: float = 0


class PacketIn(BaseModel):
    hex: str
    baseline_adc: list[int] = [0, 0, 0, 0]


@app.get("/health")
def health():
    return {
        "ok": True,
        "gait_loaded": _engine.gait_model is not None,
        "zone_loaded": _engine.zone_model is not None,
        "ulcer_loaded": _ulcer.model is not None,
        "ble_service": GATT_SERVICE_UUID,
        "device_prefix": DEVICE_NAME_PREFIX,
    }


@app.post("/v1/analyze")
def analyze(body: AnalyzeIn):
    if not body.frames or len(body.frames[0]) != 8:
        raise HTTPException(400, "frames must be (T, 8)")
    profile = ClinicalProfile(**(body.clinical.model_dump() if body.clinical else {}))
    result = _engine.analyze_window(
        body.frames,
        sample_hz=body.sample_hz,
        profile=profile,
        pressure_threshold=body.pressure_threshold,
        temperatures=body.temperatures,
        ulcer_grade=None if body.ulcer_grade is None else body.ulcer_grade - 1,
        ulcer_confidence=body.ulcer_confidence,
        compliance=body.compliance,
    )
    recs = build_recommendations(result, len(result.alerts), body.compliance)
    last = body.frames[-1]
    return {
        "health_index": result.health_index,
        "level": result.level,
        "gait_pattern": result.gait_pattern,
        "gait_confidence": result.gait_confidence,
        "high_risk_zone": result.high_risk_zone,
        "zone_confidence": result.zone_confidence,
        "iwgdf_category": result.iwgdf_category,
        "factors": result.factors,
        "extras": result.extras,
        "alerts": [a.__dict__ for a in result.alerts],
        "recommendations": recs,
        "foot_pressures": latest_frame_to_app_zones(last),
        "stepmate_prompt": stepmate_system_prompt(
            result,
            body.clinical.model_dump() if body.clinical else {},
            f"compliance={body.compliance}",
        ),
    }


@app.post("/v1/ulcer")
async def ulcer(file: UploadFile = File(...)):
    data = await file.read()
    if not data:
        raise HTTPException(400, "empty file")
    return _ulcer.predict(data)


@app.post("/v1/packet/decode")
def packet_decode(body: PacketIn):
    raw = bytes.fromhex(body.hex)
    pkt = decode_packet(raw, baseline_adc=tuple(body.baseline_adc))  # type: ignore[arg-type]
    return {
        "side": pkt.side,
        "seq": pkt.seq,
        "t_ms": pkt.t_ms,
        "kpa": pkt.kpa,
        "battery": pkt.battery,
        "temperatures_c": pkt.temperatures_c,
        "sites": pkt.as_site_map(),
    }


@app.get("/v1/protocol")
def protocol():
    demo = encode_packet("left", 1, 1000, (400, 500, 300, 600), 90).hex()
    return {
        "packet_bytes": 28,
        "sites_order": ["met1", "met2", "met5", "heel"],
        "sample_hex": demo,
        "service_uuid": GATT_SERVICE_UUID,
    }


def run():
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "8080")),
        reload=False,
    )


if __name__ == "__main__":
    run()
