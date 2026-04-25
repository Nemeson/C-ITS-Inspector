"""Synthetic PCAP-frame generators for deterministic testing.

No scapy import at module scope — constructs raw bytes directly
to avoid heavy dependencies in fast unit tests.
"""

from __future__ import annotations

import struct
from datetime import UTC, datetime
from pathlib import Path


# ─── Constants ────────────────────────────────────────────────────

ETHERTYPE_GEO_NETWORKING = 0x8947

GN_NH_BTP_B = 0x02

BTP_TYPE_DENM = 0x01
BTP_TYPE_CAM = 0x02
BTP_TYPE_SPATEM = 0x03
BTP_TYPE_MAPEM = 0x04
BTP_TYPE_SREM = 0x09
BTP_TYPE_SSEM = 0x0A

ITS_PDU_VERSION = 2


# ─── Helpers ─────────────────────────────────────────────────────

def _make_ethernet_frame(payload: bytes, ethertype: int = ETHERTYPE_GEO_NETWORKING) -> bytes:
    """Minimal Ethernet-II header + payload (no FCS)."""
    dst = b"\xff" * 6
    src = b"\x00" * 6
    return dst + src + struct.pack("!H", ethertype) + payload


def _make_geonet_header(nh: int = GN_NH_BTP_B, payload_len: int = 0) -> bytes:
    """Minimal GeoNetworking header (simplified)."""
    # Version (1) + NH (1) + Reserved (1) + LT (1) + RHL (1)
    header = bytes([1, nh, 0, 0, 10])
    # Add dummy common header fields (8 bytes)
    header += b"\x00" * 8
    # Length fields
    header += struct.pack("!H", len(header) + payload_len)
    header += struct.pack("!H", payload_len)
    return header


def _make_btp_b_header(dest_port: int, payload_len: int) -> bytes:
    """BTP-B header: dest-port (2) + dest-port-info (2)."""
    return struct.pack("!HH", dest_port, 0)


def _make_its_pdu_header(msg_id: int, station_id: int = 0x1234) -> bytes:
    """ITS-PDU-Header: version(1) + msgID(1) + stationID(4)."""
    return bytes([ITS_PDU_VERSION, msg_id]) + struct.pack("!I", station_id)


def make_its_frame(
    msg_id: int,
    payload: bytes = b"\x00" * 8,
    station_id: int = 0x1234,
    btp_port: int | None = None,
    ethertype: int = ETHERTYPE_GEO_NETWORKING,
) -> bytes:
    """Build a complete Ethernet frame carrying an ITS message.

    Args:
        msg_id: ITS PDU message ID (1=CAM, 2=DENM, 3=SPAT, 4=MAP, 9=SREM, 10=SSEM, ...)
        payload: Raw ASN.1/ITS payload bytes after the header
        station_id: 4-byte station ID
        btp_port: Optional BTP destination port (used in GeoNetworking)
        ethertype: EtherType (default GeoNetworking)
    """
    its_pdu = _make_its_pdu_header(msg_id, station_id) + payload
    if btp_port is not None:
        btp = _make_btp_b_header(btp_port, len(its_pdu))
        payload_all = btp + its_pdu
    else:
        payload_all = its_pdu

    if ethertype == ETHERTYPE_GEO_NETWORKING:
        gn = _make_geonet_header(payload_len=len(payload_all))
        payload_all = gn + payload_all

    return _make_ethernet_frame(payload_all, ethertype)


def make_cam_frame(
    station_id: int = 0x1234,
    lat: int = 52_000_000,
    lon: int = 13_000_000,
) -> bytes:
    """Minimal CAM frame with latitude/longitude."""
    # Simplified CAM payload: 4 bytes lat + 4 bytes lon
    payload = struct.pack("!ii", lat, lon)
    return make_its_frame(2, payload, station_id, btp_port=2001)


def make_denm_frame(
    station_id: int = 0x1234,
    cause_code: int = 2,
    sub_cause: int = 0,
) -> bytes:
    """Minimal DENM frame with cause code."""
    # Simplified DENM payload: cause(1) + subcause(1)
    return make_its_frame(1, bytes([cause_code, sub_cause]), station_id, btp_port=2002)


def make_map_frame(
    station_id: int = 0x1234,
    intersection_id: int = 42,
) -> bytes:
    """Minimal MAPEM frame with intersection ID."""
    payload = struct.pack("!H", intersection_id)
    return make_its_frame(4, payload, station_id, btp_port=2003)


def make_spat_frame(
    station_id: int = 0x1234,
    intersection_id: int = 42,
    signal_group: int = 7,
) -> bytes:
    """Minimal SPATEM frame."""
    payload = struct.pack("!HH", intersection_id, signal_group)
    return make_its_frame(3, payload, station_id, btp_port=2004)


def make_srem_frame(
    station_id: int = 0x1234,
    request_id: int = 1,
) -> bytes:
    """Minimal SREM frame."""
    payload = struct.pack("!H", request_id)
    return make_its_frame(9, payload, station_id, btp_port=2005)


def make_ssem_frame(
    station_id: int = 0x1234,
    request_id: int = 1,
) -> bytes:
    """Minimal SSEM frame."""
    payload = struct.pack("!H", request_id)
    return make_its_frame(10, payload, station_id, btp_port=2006)


def make_corrupted_frame(
    frame: bytes,
    truncate_last_n: int = 0,
    flip_byte_offset: int | None = None,
) -> bytes:
    """Return a corrupted variant of a frame (for robustness testing)."""
    data = bytearray(frame)
    if truncate_last_n:
        data = data[:-truncate_last_n]
    if flip_byte_offset is not None and 0 <= flip_byte_offset < len(data):
        data[flip_byte_offset] ^= 0xFF
    return bytes(data)


def write_pcap_file(path: Path, frames: list[bytes]) -> None:
    """Write a minimal PCAP file (one packet per frame)."""
    # Global header: magic(4) + version_major(2) + version_minor(2) + reserved(8) + snaplen(4) + link_type(4)
    global_header = struct.pack("!IHHiIII", 0xA1B2C3D4, 2, 4, 0, 0, 65535, 1)
    with open(path, "wb") as f:
        f.write(global_header)
        for frame in frames:
            ts = datetime.now(UTC)
            sec = int(ts.timestamp())
            usec = ts.microsecond
            incl_len = len(frame)
            orig_len = len(frame)
            pkt_header = struct.pack("!IIII", sec, usec, incl_len, orig_len)
            f.write(pkt_header)
            f.write(frame)
