import pytest

from xstep_ml.protocol import PACKET_SIZE, decode_packet, encode_packet, packet_gap_flags, packet_loss_fraction


def test_malformed_short_packet():
    with pytest.raises(ValueError, match="short packet"):
        decode_packet(b"XS")


def test_bad_magic():
    raw = encode_packet("right", 1, 10, (1, 2, 3, 4), 50)
    bad = b"NO" + raw[2:]
    with pytest.raises(ValueError, match="bad magic"):
        decode_packet(bad)


def test_missing_sensor_zero_adc():
    raw = encode_packet("left", 3, 20, (0, 0, 0, 0), 10)
    pkt = decode_packet(raw)
    assert pkt.kpa == (0.0, 0.0, 0.0, 0.0)
    assert len(raw) == PACKET_SIZE


def test_packet_loss_from_seq_gaps():
    seq = [1, 2, 3, 5, 6]
    flags = packet_gap_flags(seq)
    assert flags == [False, False, False, True, False]
    assert packet_loss_fraction(seq) == pytest.approx(0.25)
