from __future__ import annotations

from datetime import datetime, timedelta

from pcap2kml_player.data_model import (
    CaptureRole,
    MessageSource,
    MessageType,
    SessionData,
    V2xMessage,
    infer_capture_role,
)


def _make_message(
    timestamp: datetime,
    station_id: str,
    msg_type: MessageType,
    latitude: float = 52.0,
    longitude: float = 13.0,
) -> V2xMessage:
    return V2xMessage(
        timestamp=timestamp,
        station_id=station_id,
        msg_type=msg_type,
        latitude=latitude,
        longitude=longitude,
    )


def test_session_finalize_and_duration() -> None:
    base = datetime(2025, 8, 22, 12, 0, 0)
    session = SessionData()
    session.add_message(_make_message(base + timedelta(seconds=3), "B", MessageType.SPATEM))
    session.add_message(_make_message(base, "A", MessageType.CAM))
    session.add_message(_make_message(base + timedelta(seconds=1), "A", MessageType.MAPEM))

    session.finalize()

    assert [msg.station_id for msg in session.messages] == ["A", "A", "B"]
    assert session.duration_seconds == 3
    assert session.time_range == (base, base + timedelta(seconds=3))


def test_filter_messages_by_type_and_station() -> None:
    base = datetime(2025, 8, 22, 12, 0, 0)
    session = SessionData()
    cam = _make_message(base, "station-a", MessageType.CAM)
    spatem = _make_message(base + timedelta(seconds=1), "station-b", MessageType.SPATEM)
    mapem = _make_message(base + timedelta(seconds=2), "station-a", MessageType.MAPEM)

    for msg in [cam, spatem, mapem]:
        session.add_message(msg)

    filtered = session.filter_messages(
        active_types={MessageType.CAM, MessageType.MAPEM},
        active_stations={"station-a"},
    )

    assert filtered == [cam, mapem]


def test_kml_description_contains_optional_fields() -> None:
    msg = V2xMessage(
        timestamp=datetime(2025, 8, 22, 12, 0, 0),
        station_id="car-7",
        msg_type=MessageType.CAM,
        latitude=52.4280646,
        longitude=13.5282899,
        altitude=34.2,
        speed=12.3,
        heading=182.0,
    )

    description = msg.to_kml_description()

    assert "car-7" in description
    assert "52.428065" in description
    assert "34.2 m" in description
    assert "12.3 m/s" in description


def test_detail_rows_surface_identity_hint_early() -> None:
    msg = V2xMessage(
        timestamp=datetime(2025, 8, 22, 12, 0, 0),
        station_id="car-7",
        msg_type=MessageType.CAM,
        latitude=52.4280646,
        longitude=13.5282899,
        details={
            "Identitaets-Hinweis": "Einzelne CAM-Station-ID weicht von der dominanten Session-ID ab",
            "Quelle": "lpv",
        },
    )

    rows = msg.to_detail_rows()

    assert rows[4][0] == "Identitaets-Hinweis"
    assert "dominanten Session-ID" in rows[4][1]
    assert rows[-1] == ("Quelle", "lpv")


def test_infer_capture_role_from_txa_rxa_filenames() -> None:
    assert infer_capture_role("txa_22082025.pcap") == CaptureRole.TXA
    assert infer_capture_role("rsu_rxa.pcap") == CaptureRole.RXA
    assert infer_capture_role("neutral.pcap") == CaptureRole.UNKNOWN


def test_detail_rows_include_source_and_merge_metadata() -> None:
    msg = V2xMessage(
        timestamp=datetime(2025, 8, 22, 12, 0, 0),
        station_id="car-7",
        msg_type=MessageType.SREM,
        latitude=52.0,
        longitude=13.0,
        source=MessageSource(
            path="C:/captures/txa_case.pcap",
            filename="txa_case.pcap",
            source_index=0,
            role=CaptureRole.TXA,
            parser_backend="scapy",
        ),
        merge_group_id="merge-00001",
        merge_confidence=0.94,
        merge_reason="Request-Key gleich",
    )

    rows = dict(msg.to_detail_rows())

    assert rows["Capture-Datei"] == "txa_case.pcap"
    assert rows["Capture-Rolle"] == "TXA"
    assert rows["Parser"] == "scapy"
    assert "merge-00001" in rows["Merge-Gruppe"]
    assert "0.94" in rows["Merge-Gruppe"]
