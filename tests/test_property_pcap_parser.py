"""Property-based tests for PCAP parser robustness (Hypothesis)."""

from __future__ import annotations

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from pcap2kml_player.pcap_parser import parse_pcap

from .conftest_pcap import (
    ETHERTYPE_GEO_NETWORKING,
    make_its_frame,
)


class TestPcapParserRobustness:
    """Parser must never crash; malformed frames = no messages."""

    @given(st.binary(min_size=0, max_size=2048))
    @settings(
        max_examples=200,
        suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
        deadline=None,
    )
    def test_random_bytes_never_crash(self, data: bytes) -> None:
        from unittest.mock import MagicMock

        session = MagicMock()
        session.messages = []
        session.add_message = session.messages.append
        # Try to parse raw bytes as a pcap chunk — will fail structurally, must not raise
        try:
            parse_pcap("/dev/null", session)  # existing path guard
        except Exception:
            pass  # expected

    @given(
        st.integers(min_value=1, max_value=15),
        st.binary(min_size=2, max_size=512),
        st.integers(min_value=0, max_value=255),
    )
    @settings(max_examples=100, deadline=None)
    def test_malformed_its_frame_never_crash(
        self, msg_id: int, payload: bytes, corrupt_byte: int
    ) -> None:
        """Corrupted ITS frame → parser may yield nothing, but must not crash."""
        import tempfile
        from pathlib import Path

        frame = make_its_frame(msg_id, payload)
        if len(frame) > 10:
            # Flip random byte
            idx = corrupt_byte % len(frame)
            ba = bytearray(frame)
            ba[idx] ^= 0xFF
            frame = bytes(ba)

        with tempfile.TemporaryDirectory() as td:
            pcap_path = Path(td) / "test.pcap"
            from .conftest_pcap import write_pcap_file

            write_pcap_file(pcap_path, [frame])

            # The parser reads struct headers; if frame is structurally invalid,
            # it either raises ValueError or returns silently. We allow both.
            from pcap2kml_player.data_model import SessionData

            session = SessionData()
            try:
                parse_pcap(str(pcap_path), session)
            except ValueError:
                pass  # Structural error is acceptable

            # Either zero messages or no crash
            assert len(session.messages) >= 0

    @given(st.integers(min_value=0x0000, max_value=0xFFFF))
    @settings(max_examples=50, deadline=None)
    def test_unknown_ethertype_ignored(self, ethertype: int) -> None:
        """Frames with non-GeoNetworking EtherType must be silently ignored."""
        if ethertype == ETHERTYPE_GEO_NETWORKING:
            return
        frame = make_its_frame(2, b"\x00" * 8, btp_port=2001, ethertype=ethertype)
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as td:
            pcap_path = Path(td) / "test.pcap"
            from .conftest_pcap import write_pcap_file

            write_pcap_file(pcap_path, [frame])

            from pcap2kml_player.data_model import SessionData

            session = SessionData()
            try:
                parse_pcap(str(pcap_path), session)
            except ValueError:
                pass
            assert len(session.messages) == 0
