"""Unit tests for security_parser heuristic field extraction.

Targets low-coverage areas identified in inventory (52.7% line, ~45% branch).
"""

from __future__ import annotations

import pytest

from pcap2kml_player.security_parser import (
    _bytes_to_hex,
    _read_fixed_length,
    _read_length_determinant,
    _read_uint16,
    _read_uint8,
    _scan_assurance_level,
    _scan_its_aid,
    _scan_region,
    _scan_station_type,
    _scan_validity_period,
)


class TestLowLevelHelpers:
    def test_read_uint8_normal(self):
        assert _read_uint8(b"\x42\x00\x00", 0) == (0x42, 1)

    def test_read_uint8_eof(self):
        assert _read_uint8(b"", 0) == (0, 0)

    def test_read_uint16(self):
        assert _read_uint16(b"\x01\x02", 0) == (0x0102, 2)

    def test_read_length_small(self):
        assert _read_length_determinant(b"\x0a", 0) == (10, 1)

    def test_read_length_large(self):
        data = bytes([0x80 | 0x01, 0x2A])  # length = 0x012A = 298
        assert _read_length_determinant(data, 0) == (298, 2)

    def test_read_fixed_length(self):
        assert _read_fixed_length(b"1234567890", 2, 4) == (b"3456", 6)

    def test_bytes_to_hex(self):
        assert _bytes_to_hex(b"\xde\xad", max_len=4) == "dead"


class TestAssuranceScanner:
    def test_finds_assurance(self):
        # Byte with level=3 (bits 5-7) and confidence=2 (bits 0-2) → 0b011_00010 = 0x62
        data = bytes([0x00, 0x62, 0x00])
        assert _scan_assurance_level(data, 0, 3) == 3

    def test_ignores_ascii(self):
        # Bytes <= 0x0F are treated as non-certificate data → ignored
        data = bytes([0x05, 0x00, 0x00])
        assert _scan_assurance_level(data, 0, 3) is None


class TestStationTypeScanner:
    def test_finds_passenger_car(self):
        # stationType=5 → passengerCar
        # Need byte at position where offset+1 < end and data[offset+1] < 128
        data = bytes([0xFF, 0x05, 0x00])
        assert _scan_station_type(data, 0, 3) == "passengerCar"

    def test_ignores_unknown(self):
        data = bytes([0x00, 0x80])
        # 0x00 is "unknown" but next byte 0x80 is NOT < 128
        assert _scan_station_type(data, 0, 2) is None


class TestValidityScanner:
    def test_finds_validity(self):
        # Time32 = 1000 seconds since 2004-01-01 → ~2004-01-01 00:16:40
        data = struct.pack("!I", 1000) + b"\x00"  # duration: 1 sec
        start, end = _scan_validity_period(data, 0, 5)
        assert start is not None
        assert "seconds" in end

    def test_no_match(self):
        data = b"\xff" * 10
        assert _scan_validity_period(data, 0, 10) == (None, None)


class TestItsAidScanner:
    def test_finds_denm(self):
        data = bytes([0x00, 0x24, 0x00])  # ITS-AID DENM = 0x24
        assert 0x00000024 in _scan_its_aid(data, 0, 3)

    def test_empty(self):
        assert _scan_its_aid(b"", 0, 0) is None


class TestRegionScanner:
    def test_country(self):
        data = bytes([4, ord("D"), ord("E")])
        assert _scan_region(data, 0, 3) == ("country", "DE")

    def test_none(self):
        data = bytes([0])
        assert _scan_region(data, 0, 1) == ("none", None)

    def test_unknown(self):
        assert _scan_region(b"", 0, 0) == (None, None)


# struct delayed import to avoid circular at module scope
import struct  # noqa: E402
