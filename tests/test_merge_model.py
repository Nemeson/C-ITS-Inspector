from __future__ import annotations

from datetime import UTC, datetime, timedelta

from pcap2kml_player.data_model import (
    CaptureRole,
    MessageSource,
    MessageType,
    SessionData,
    V2xMessage,
)
from pcap2kml_player.merge_model import build_merge_groups, score_merge_candidate


def _source(filename: str, role: CaptureRole) -> MessageSource:
    return MessageSource(
        path=f"C:/captures/{filename}",
        filename=filename,
        source_index=0 if role == CaptureRole.TXA else 1,
        role=role,
        parser_backend="scapy",
    )


def _srem(timestamp: datetime, source: MessageSource, lat: float = 52.0) -> V2xMessage:
    return V2xMessage(
        timestamp=timestamp,
        station_id="bus-7",
        msg_type=MessageType.SREM,
        latitude=lat,
        longitude=13.0,
        raw_payload=b"same-request",
        source=source,
        decoded_data={
            "intersectionId": 42,
            "requestId": 11,
            "sequenceNumber": 2,
            "importanceLevel": 12,
        },
    )


def _cam(timestamp: datetime, source: MessageSource, lat: float) -> V2xMessage:
    return V2xMessage(
        timestamp=timestamp,
        station_id="7153",
        msg_type=MessageType.CAM,
        latitude=lat,
        longitude=13.0,
        speed=12.0,
        heading=90.0,
        source=source,
        decoded_data={"stationId": 7153},
    )


def test_build_merge_groups_merges_txa_rxa_srem_by_request_key() -> None:
    now = datetime(2026, 4, 20, 12, 0, 0, tzinfo=UTC)
    messages = [
        _srem(now, _source("txa_case.pcap", CaptureRole.TXA)),
        _srem(now + timedelta(milliseconds=80), _source("rxa_case.pcap", CaptureRole.RXA)),
    ]

    groups = build_merge_groups(messages)

    assert len(groups) == 1
    assert messages[0].merge_group_id == messages[1].merge_group_id
    assert messages[0].merge_confidence is not None
    assert messages[0].merge_confidence >= 0.85
    assert "Request-Key gleich" in messages[0].merge_reason


def test_score_merge_candidate_rejects_far_apart_cam_messages() -> None:
    now = datetime(2026, 4, 20, 12, 0, 0, tzinfo=UTC)
    left = _cam(now, _source("txa_case.pcap", CaptureRole.TXA), 52.0)
    right = _cam(now + timedelta(milliseconds=50), _source("rxa_case.pcap", CaptureRole.RXA), 52.01)

    score, reason = score_merge_candidate(left, right)

    assert score < 0.72
    assert "auseinander" in reason


def test_session_canonical_messages_keeps_one_message_per_merge_group() -> None:
    now = datetime(2026, 4, 20, 12, 0, 0, tzinfo=UTC)
    tx = _srem(now, _source("txa_case.pcap", CaptureRole.TXA))
    rx = _srem(now + timedelta(milliseconds=80), _source("rxa_case.pcap", CaptureRole.RXA))
    unrelated = _cam(now + timedelta(seconds=1), _source("txa_case.pcap", CaptureRole.TXA), 52.0)
    session = SessionData(messages=[rx, unrelated, tx])
    for msg in session.messages:
        session.station_ids.add(msg.station_id)
        session.msg_type_counts[msg.msg_type] = session.msg_type_counts.get(msg.msg_type, 0) + 1

    session.finalize()

    canonical = session.canonical_messages()

    assert len(canonical) == 2
    assert {msg.msg_type for msg in canonical} == {MessageType.SREM, MessageType.CAM}
