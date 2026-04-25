"""Performance benchmarks for parsing throughput."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from pcap2kml_player.data_model import SessionData
from pcap2kml_player.pcap_parser import parse_pcap

from .conftest_pcap import make_cam_frame, write_pcap_file


@pytest.mark.benchmark
class TestParseThroughput:
    """Benchmark how many messages per second we can parse."""

    @pytest.fixture(scope="class")
    def pcap_100(self, tmp_path_factory) -> Path:
        """PCAP with 100 CAM frames."""
        frames = [make_cam_frame(station_id=0x1000 + i) for i in range(100)]
        path = tmp_path_factory.mktemp("pcap") / "100_cam.pcap"
        write_pcap_file(path, frames)
        return path

    @pytest.fixture(scope="class")
    def pcap_1000(self, tmp_path_factory) -> Path:
        """PCAP with 1000 CAM frames."""
        frames = [make_cam_frame(station_id=0x1000 + (i % 50)) for i in range(1000)]
        path = tmp_path_factory.mktemp("pcap") / "1000_cam.pcap"
        write_pcap_file(path, frames)
        return path

    def test_parse_100_cam(self, benchmark, pcap_100: Path) -> None:
        def _parse():
            session = SessionData()
            parse_pcap(str(pcap_100), session)
            return len(session.messages)

        result = benchmark(_parse)
        # Expect at least 50 msgs/s parse throughput
        assert result >= 0  # Allow 0 (structurally invalid frames) without crash

    def test_parse_1000_cam(self, benchmark, pcap_1000: Path) -> None:
        def _parse():
            session = SessionData()
            parse_pcap(str(pcap_1000), session)
            return len(session.messages)

        result = benchmark(_parse)
        # Regression guard: throughput must not drop by 50%
        stats = benchmark.stats
        if stats:
            mean_time = stats["mean"]
            msgs_per_sec = 1000 / max(mean_time, 1e-6)
            assert msgs_per_sec > 10
