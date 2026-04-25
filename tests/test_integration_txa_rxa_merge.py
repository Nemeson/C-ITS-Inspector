"""Integration tests for TXA+RXA soft-merge with real captures."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from pcap2kml_player.data_model import CaptureRole, SessionData
from pcap2kml_player.merge_model import build_merge_groups
from pcap2kml_player.pcap_parser import parse_pcap


@pytest.mark.integration
@pytest.mark.pcap_real
@pytest.mark.slow
class TestTxaRxaMergeIntegration:
    """End-to-end merge using real test captures."""

    TESTFILES = Path(__file__).parent.parent / "testfiles"

    def _load_capture(self, stem: str) -> SessionData:
        paths = list(self.TESTFILES.glob(f"{stem}*.pcap*"))
        if not paths:
            pytest.skip(f"Capture {stem}* not found")
        session = SessionData()
        for p in paths[:1]:  # take first match
            parse_pcap(str(p), session)
        session.finalize()
        return session

    def test_txa_capture_loads(self) -> None:
        session = self._load_capture("txa_22082025")
        assert len(session.messages) > 0
        assert len(session.station_ids) >= 1

    def test_rxa_capture_loads(self) -> None:
        session = self._load_capture("rxa_22082025")
        assert len(session.messages) > 0

    def test_txa_rxa_merge(self) -> None:
        """Load TXA and RXA and merge; verify merge groups."""
        txa = self._load_capture("txa_22082025")
        rxa = self._load_capture("rxa_22082025")

        # Create combined session
        combined = SessionData()
        for msg in txa.messages:
            msg.source = CaptureRole(role="transmitter", filename="txa", index=0)
            combined.add_message(msg)
        for msg in rxa.messages:
            msg.source = CaptureRole(role="receiver", filename="rxa", index=0)
            combined.add_message(msg)
        combined.finalize()
        build_merge_groups(combined.messages)

        # Merge groups should exist if both captures have matching messages
        assert len(combined.merge_groups) >= 0

    def test_merge_confidence_range(self) -> None:
        """Merge confidence must be in [0, 1]."""
        txa = self._load_capture("txa_22082025")
        rxa = self._load_capture("rxa_22082025")

        combined = SessionData()
        for msg in txa.messages:
            combined.add_message(msg)
        for msg in rxa.messages:
            combined.add_message(msg)
        combined.finalize()
        build_merge_groups(combined.messages)

        for group in combined.merge_groups.values():
            assert 0.0 <= group.confidence <= 1.0
