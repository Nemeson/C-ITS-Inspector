from __future__ import annotations

from datetime import datetime, timedelta

from pcap2kml_player.data_model import MessageType, SessionData, V2xMessage
from pcap2kml_player.player_controller import PlayerController


def _message(ts: datetime, station: str = "station") -> V2xMessage:
    return V2xMessage(
        timestamp=ts,
        station_id=station,
        msg_type=MessageType.CAM,
        latitude=52.0,
        longitude=13.0,
    )


def test_player_advances_across_gaps_larger_than_single_tick() -> None:
    base = datetime(2025, 8, 22, 12, 0, 0)
    session = SessionData(
        messages=[
            _message(base),
            _message(base + timedelta(milliseconds=150)),
            _message(base + timedelta(milliseconds=320)),
        ]
    )

    controller = PlayerController()
    controller.set_session(session)
    controller.play()

    for _ in range(4):
        controller._on_tick()

    assert controller.current_index >= 1
    assert controller.get_current_playback_time() >= 0.15


def test_seek_updates_playback_time() -> None:
    base = datetime(2025, 8, 22, 12, 0, 0)
    session = SessionData(
        messages=[
            _message(base),
            _message(base + timedelta(seconds=2)),
            _message(base + timedelta(seconds=5)),
        ]
    )

    controller = PlayerController()
    controller.set_session(session)
    controller.seek_to_index(2)

    assert controller.current_index == 2
    assert controller.get_current_playback_time() == 5.0
