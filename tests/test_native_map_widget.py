"""Tests for NativeMapWidget helper functions."""

from datetime import datetime, timezone

from pcap2kml_player.data_model import MessageType, V2xMessage
from pcap2kml_player.native_map_widget import (
    _bounds_for_messages,
    _has_display_position,
    _project_message,
)


def _msg(lat: float, lon: float, station_id: str = "s1") -> V2xMessage:
    return V2xMessage(
        msg_type=MessageType.CAM,
        station_id=station_id,
        latitude=lat,
        longitude=lon,
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


# ---------------------------------------------------------------------------
# _has_display_position
# ---------------------------------------------------------------------------


def test_has_display_position_valid():
    assert _has_display_position(_msg(48.7758, 9.1829)) is True


def test_has_display_position_zero_zero():
    assert _has_display_position(_msg(0.0, 0.0)) is False


def test_has_display_position_out_of_range_lat():
    assert _has_display_position(_msg(91.0, 9.0)) is False


def test_has_display_position_out_of_range_lon():
    assert _has_display_position(_msg(48.0, 181.0)) is False


# ---------------------------------------------------------------------------
# _bounds_for_messages
# ---------------------------------------------------------------------------


def test_bounds_for_messages_empty_returns_none():
    assert _bounds_for_messages([]) is None


def test_bounds_for_messages_single_message_expands_bounds():
    bounds = _bounds_for_messages([_msg(48.0, 9.0)])
    assert bounds is not None
    min_lat, max_lat, min_lon, max_lon = bounds
    assert min_lat < 48.0 < max_lat
    assert min_lon < 9.0 < max_lon


def test_bounds_for_messages_multiple_messages():
    msgs = [_msg(48.0, 9.0), _msg(49.0, 10.0)]
    bounds = _bounds_for_messages(msgs)
    assert bounds == (48.0, 49.0, 9.0, 10.0)


# ---------------------------------------------------------------------------
# _project_message
# ---------------------------------------------------------------------------


def test_project_message_center_maps_to_midpoint():
    bounds = (47.0, 49.0, 8.0, 10.0)
    msg = _msg(48.0, 9.0)
    _, (px, py) = _project_message(msg, bounds)
    assert 590 < px < 610
    assert 390 < py < 410


def test_project_message_returns_same_message_object():
    bounds = (47.0, 49.0, 8.0, 10.0)
    msg = _msg(48.0, 9.0)
    returned_msg, _ = _project_message(msg, bounds)
    assert returned_msg is msg
