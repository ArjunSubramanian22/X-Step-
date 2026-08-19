import json
from pathlib import Path

from research.import_real_data import anonymize_subject, import_raw, import_session_folder


def test_anonymize_stable_and_not_raw():
    a = anonymize_subject("alice")
    b = anonymize_subject("alice")
    assert a == b
    assert a.startswith("S")
    assert "alice" not in a


def test_import_csv_session(tmp_path: Path):
    raw = tmp_path / "raw"
    sess = raw / "walk01"
    sess.mkdir(parents=True)
    (sess / "session.json").write_text(
        json.dumps(
            {
                "subject_id": "volunteer-A",
                "session_id": "walk01",
                "foot_side": "both",
                "footwear": "athletic",
                "hardware_revision": "esp32-dev-fsr402-4ch",
                "firmware_version": "insole-protocol-v1",
                "calibration_version": "linear_adc_engineering_v0",
                "sample_hz": 25,
                "notes": "",
            }
        )
    )
    lines = ["timestamp_ns,seq,foot_side,met1_adc,met2_adc,met5_adc,heel_adc"]
    for i in range(8):
        lines.append(f"{i * 40_000_000},{i},left,400,500,300,600")
        lines.append(f"{i * 40_000_000},{i},right,410,510,310,610")
    (sess / "traces.csv").write_text("\n".join(lines) + "\n")
    info = import_session_folder(sess)
    assert info["subject_id"].startswith("S")
    assert info["subject_id"] != "volunteer-A"
    assert info["n_samples"] == 8
    rec = info["records"][0]
    assert rec["data_source"] == "human"
    assert rec["raw_adc"] is not None

    proc = tmp_path / "processed"
    payload = import_raw(raw, proc)
    assert payload["n_sessions_imported"] == 1
    dest = proc / payload["run_id"]
    assert dest.is_dir()
    raw_csv = (sess / "traces.csv").read_text()
    import_raw(raw, proc)  # second run new id
    assert (sess / "traces.csv").read_text() == raw_csv
    runs = list(proc.iterdir())
    assert len(runs) == 2
