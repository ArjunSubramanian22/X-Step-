from fastapi.testclient import TestClient

from api.main import app
from xstep_ml.protocol import encode_packet

client = TestClient(app)


def test_health_endpoint():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_analyze_window_disclaimer():
    frames = [[10.0] * 8 for _ in range(12)]
    r = client.post("/v1/analyze", json={"frames": frames, "sample_hz": 25})
    assert r.status_code == 200
    body = r.json()
    assert "Not a medical diagnosis" in body["disclaimer"]
    assert body["risk_source"] == "deterministic_engine"
    assert "contributions" in body
    assert body["health_index"] >= 0


def test_analyze_rejects_wrong_shape():
    r = client.post("/v1/analyze", json={"frames": [[1, 2, 3]], "sample_hz": 25})
    assert r.status_code == 400


def test_packet_decode_endpoint():
    raw = encode_packet("left", 9, 500, (100, 200, 150, 300), 80)
    r = client.post("/v1/packet/decode", json={"hex": raw.hex()})
    assert r.status_code == 200
    assert r.json()["side"] == "left"
    assert r.json()["seq"] == 9
