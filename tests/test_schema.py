import numpy as np
import pytest

from xstep_ml.data.schema import (
    CHANNEL_ORDER,
    PressureWindowRecord,
    assert_channel_names,
    frames_to_samples,
    normalize_location,
    validate_records,
    validate_window_array,
)


def test_location_aliases():
    assert normalize_location("toes") == "met1"
    assert normalize_location("ball") == "met2"
    assert normalize_location("arch") == "met5"
    assert normalize_location("1st metatarsal") == "met1"


def test_channel_order():
    assert_channel_names(CHANNEL_ORDER)
    with pytest.raises(ValueError):
        assert_channel_names(["heel", "met1"])


def test_window_validation_and_samples():
    frames = np.ones((4, 8)) * 10.0
    validate_window_array(frames)
    samples = frames_to_samples(
        subject_id="s1",
        session_id="sess",
        frames_kpa=frames,
        sample_hz=25.0,
        calibration_version="v0",
        firmware_version="sim",
    )
    assert len(samples) == 4 * 8
    assert samples[0].sensor_location == "met1"
    rec = PressureWindowRecord(
        subject_id="s1",
        session_id="sess",
        sample_hz=25,
        calibration_version="v0",
        firmware_version="sim",
        pressure_kpa=frames.tolist(),
        packet_loss_frac=0.0,
        data_source="synthetic",
    )
    assert validate_records([rec]) == 1


def test_negative_pressure_rejected():
    with pytest.raises(ValueError):
        validate_window_array(np.array([[-1.0] * 8]))
