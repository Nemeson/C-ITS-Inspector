from __future__ import annotations

from pathlib import Path

from pcap2kml_player.data_model import MessageType
from pcap2kml_player.pcap_parser import parse_pcap


TESTFILES = Path(__file__).resolve().parent.parent / "testfiles"


def test_parse_srem_with_ocit_pcap() -> None:
    session = parse_pcap(str(TESTFILES / "SREM with OCIT.pcap"))

    assert session.messages
    assert session.msg_type_counts[MessageType.SREM] > 0
    assert any(53.0 < msg.latitude < 54.0 for msg in session.messages)
    assert any(10.0 < msg.longitude < 11.0 for msg in session.messages)


def test_parse_rxa_22082025_pcap() -> None:
    session = parse_pcap(str(TESTFILES / "rxa_22082025.pcap"))

    assert session.messages
    assert MessageType.MAPEM in session.msg_type_counts
    assert len(session.station_ids) >= 1


def test_parse_txa_22082025_pcap() -> None:
    session = parse_pcap(str(TESTFILES / "txa_22082025.pcap"))

    assert session.messages
    assert session.msg_type_counts[MessageType.SPATEM] > 0
    assert any(52.0 < msg.latitude < 53.0 for msg in session.messages)
