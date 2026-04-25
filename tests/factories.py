"""Builder/Factory for V2xMessage and SessionData in tests.

Replaces scattered `_make_msg()` helpers across 8+ test files.
Usage:
    from tests.factories import V2xMessageBuilder
    msg = V2xMessageBuilder().cam().at(52, 13).with_speed(50).build()
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Self

from pcap2kml_player.data_model import MessageType, SessionData, V2xMessage


@dataclass
class V2xMessageBuilder:
    """Fluent builder for V2xMessage test instances."""

    _timestamp: datetime = field(default_factory=lambda: datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC))
    _station_id: str = "veh-1"
    _msg_type: MessageType = MessageType.CAM
    _latitude: float = 52.0
    _longitude: float = 13.0
    _altitude: float | None = None
    _heading: float | None = None
    _speed: float | None = None
    _details: dict[str, str] = field(default_factory=dict)
    _decoded_data: dict = field(default_factory=dict)
    _raw_payload: bytes | None = None

    # --- type shortcuts ---
    def cam(self) -> Self:
        self._msg_type = MessageType.CAM
        return self

    def denm(self) -> Self:
        self._msg_type = MessageType.DENM
        return self

    def mapem(self) -> Self:
        self._msg_type = MessageType.MAPEM
        return self

    def spatem(self) -> Self:
        self._msg_type = MessageType.SPATEM
        return self

    def srem(self) -> Self:
        self._msg_type = MessageType.SREM
        return self

    def ssem(self) -> Self:
        self._msg_type = MessageType.SSEM
        return self

    def nmea(self) -> Self:
        self._msg_type = MessageType.NMEA
        return self

    # --- field setters ---
    def at(self, lat: float, lon: float) -> Self:
        self._latitude = lat
        self._longitude = lon
        return self

    def with_altitude(self, alt: float) -> Self:
        self._altitude = alt
        return self

    def with_heading(self, heading: float) -> Self:
        self._heading = heading
        return self

    def with_speed(self, speed: float) -> Self:
        self._speed = speed
        return self

    def with_station(self, station_id: str) -> Self:
        self._station_id = station_id
        return self

    def at_time(self, timestamp: datetime) -> Self:
        self._timestamp = timestamp
        return self

    def with_details(self, **kwargs: str) -> Self:
        self._details.update(kwargs)
        return self

    def with_decoded(self, data: dict) -> Self:
        self._decoded_data = data
        return self

    def with_raw_payload(self, payload: bytes) -> Self:
        self._raw_payload = payload
        return self

    # --- build ---
    def build(self) -> V2xMessage:
        return V2xMessage(
            timestamp=self._timestamp,
            station_id=self._station_id,
            msg_type=self._msg_type,
            latitude=self._latitude,
            longitude=self._longitude,
            altitude=self._altitude,
            heading=self._heading,
            speed=self._speed,
            details=self._details,
            decoded_data=self._decoded_data,
            raw_payload=self._raw_payload,
        )


def build_cam_session(n: int = 10) -> SessionData:
    """SessionData with n CAM messages (1 per second)."""
    session = SessionData()
    base = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
    for i in range(n):
        msg = (
            V2xMessageBuilder()
            .cam()
            .at(52.0 + i * 0.001, 13.0 + i * 0.001)
            .with_speed(float(i * 10))
            .with_heading(float(i * 36))
            .at_time(base + timedelta(seconds=i))
            .build()
        )
        session.add_message(msg)
    session.finalize(build_merge_groups=False)
    return session


# Delayed import to avoid circularity in module scope
from datetime import timedelta  # noqa: E402
