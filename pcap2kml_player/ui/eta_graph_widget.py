"""ETA analysis graph for PCAP2KML Player."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QWidget

from ..data_model import MessageType, V2xMessage
from ..scene_model import build_scene_snapshot


@dataclass(frozen=True)
class EtaPoint:
    """One received ETA sample from an SREM/SRM message."""

    timestamp: datetime
    remaining_seconds: float
    label: str


@dataclass(frozen=True)
class SpeedPoint:
    """One speed sample for the selected vehicle."""

    timestamp: datetime
    speed_mps: float


@dataclass(frozen=True)
class RequestEvent:
    """One SRM/SREM or SSEM event marker in the ETA graph."""

    timestamp: datetime
    kind: str
    label: str
    color: QColor


class EtaGraphWidget(QWidget):
    """Paint a compact ETA, speed, and request-response timeline."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._messages: list[V2xMessage] = []
        self._station_id: Optional[str] = None
        self._current_time: Optional[datetime] = None
        self._eta_points: list[EtaPoint] = []
        self._speed_points: list[SpeedPoint] = []
        self._events: list[RequestEvent] = []
        self.setMinimumHeight(260)
        self.setStyleSheet("background: #ffffff; border: 1px solid #d7dde8; border-radius: 12px;")

    def set_messages(self, messages: list[V2xMessage]) -> None:
        """Set the full message stream used for graph extraction."""
        self._messages = messages
        self._rebuild_series()

    def set_station(self, station_id: Optional[str]) -> None:
        """Select the vehicle/station to render."""
        self._station_id = station_id
        self._rebuild_series()

    def set_current_time(self, timestamp: Optional[datetime]) -> None:
        """Move the playback cursor."""
        self._current_time = timestamp
        self.update()

    def summary_text(self) -> str:
        """Return a short operator-facing summary for the selected station."""
        if not self._station_id:
            return "Kein Fahrzeug ausgewaehlt."
        return (
            f"Fahrzeug {self._station_id}: "
            f"{len(self._eta_points)} ETA-Sample(s), "
            f"{len(self._speed_points)} Speed-Sample(s), "
            f"{len(self._events)} SRM/SSEM-Ereignis(se)."
        )

    def _rebuild_series(self) -> None:
        self._eta_points = []
        self._speed_points = []
        self._events = []

        if not self._messages or not self._station_id:
            self.update()
            return

        for msg in self._messages:
            if msg.station_id == self._station_id and msg.speed is not None:
                self._speed_points.append(SpeedPoint(msg.timestamp, float(msg.speed)))

            if msg.station_id == self._station_id and msg.msg_type == MessageType.SREM:
                eta = _coerce_eta_datetime(msg.decoded_data.get("eta"), msg.timestamp)
                request_id = _coerce_int(msg.decoded_data.get("requestId"))
                sequence_number = _coerce_int(msg.decoded_data.get("sequenceNumber"))
                remaining_seconds = (eta - msg.timestamp).total_seconds() if eta else 0.0
                label = _request_label("SRM", request_id, sequence_number)
                self._events.append(
                    RequestEvent(
                        timestamp=msg.timestamp,
                        kind="SRM",
                        label=label if eta is None else f"{label} ETA {remaining_seconds:.1f}s",
                        color=QColor("#2563eb"),
                    )
                )
                if eta is not None:
                    self._eta_points.append(
                        EtaPoint(
                            timestamp=msg.timestamp,
                            remaining_seconds=remaining_seconds,
                            label=label,
                        )
                    )

        scene = build_scene_snapshot(self._messages, self._messages[-1].timestamp)
        for request in scene.request_states:
            if request.station_id != self._station_id or request.responded_at is None:
                continue
            status = request.ssem_status or "acknowledged"
            self._events.append(
                RequestEvent(
                    timestamp=request.responded_at,
                    kind="SSEM",
                    label=f"SSEM {request.request_id}/{request.sequence_number}: {status}",
                    color=_status_color(status),
                )
            )

        self._eta_points.sort(key=lambda point: point.timestamp)
        self._speed_points.sort(key=lambda point: point.timestamp)
        self._events.sort(key=lambda event: event.timestamp)
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt override
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.fillRect(rect, QColor("#ffffff"))

        if not self._messages:
            self._draw_empty_state(painter, "Keine PCAP-Sitzung geladen.")
            return
        if not self._station_id:
            self._draw_empty_state(painter, "Bitte ein Fahrzeug fuer die ETA-Analyse auswaehlen.")
            return

        start_time = self._messages[0].timestamp
        end_time = self._messages[-1].timestamp
        duration = max(1.0, (end_time - start_time).total_seconds())
        plot = QRectF(58, 28, max(120, self.width() - 128), max(120, self.height() - 78))

        eta_max = max([point.remaining_seconds for point in self._eta_points] + [1.0])
        speed_max = max([point.speed_mps for point in self._speed_points] + [1.0])

        self._draw_grid(painter, plot, duration, eta_max, speed_max)

        for request_event in self._events:
            x = _x_for_time(request_event.timestamp, start_time, duration, plot)
            painter.setPen(QPen(request_event.color, 1.5, Qt.PenStyle.DashLine))
            painter.drawLine(QPointF(x, plot.top()), QPointF(x, plot.bottom()))
            painter.setPen(QPen(request_event.color, 1))
            painter.setFont(QFont("Segoe UI", 8, QFont.Weight.DemiBold))
            painter.drawText(QPointF(x + 4, plot.top() + 14), request_event.kind)
            painter.setFont(QFont("Segoe UI", 8))
            label = painter.fontMetrics().elidedText(
                request_event.label,
                Qt.TextElideMode.ElideRight,
                118,
            )
            painter.drawText(QPointF(x + 4, plot.bottom() - 8), label)

        self._draw_eta_series(painter, plot, start_time, duration, eta_max)
        self._draw_speed_series(painter, plot, start_time, duration, speed_max)
        self._draw_current_cursor(painter, plot, start_time, duration)
        self._draw_legend(painter, plot)

        if not self._eta_points and not self._speed_points and not self._events:
            self._draw_empty_state(
                painter,
                "Fuer dieses Fahrzeug wurden noch keine ETA-, Speed- oder SRM/SSEM-Daten gefunden.",
            )

    def _draw_empty_state(self, painter: QPainter, text: str) -> None:
        painter.setPen(QPen(QColor("#667891")))
        painter.setFont(QFont("Segoe UI", 10))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, text)

    def _draw_grid(
        self,
        painter: QPainter,
        plot: QRectF,
        duration: float,
        eta_max: float,
        speed_max: float,
    ) -> None:
        painter.setPen(QPen(QColor("#d7dde8"), 1))
        painter.drawRect(plot)
        painter.setFont(QFont("Segoe UI", 8))

        for index in range(1, 5):
            y = plot.top() + (plot.height() * index / 5)
            painter.setPen(QPen(QColor("#edf2f7"), 1))
            painter.drawLine(QPointF(plot.left(), y), QPointF(plot.right(), y))

        painter.setPen(QPen(QColor("#7b8ca4")))
        for index in range(6):
            x = plot.left() + (plot.width() * index / 5)
            y = plot.bottom() + 16
            painter.drawLine(QPointF(x, plot.bottom()), QPointF(x, plot.bottom() + 4))
            painter.drawText(QPointF(x - 14, y), f"{duration * index / 5:.0f}s")

        painter.drawText(QPointF(plot.left() - 52, plot.top() + 10), f"{eta_max:.0f}s ETA")
        painter.drawText(QPointF(plot.right() + 8, plot.top() + 10), f"{speed_max:.1f} m/s")
        painter.drawText(QPointF(plot.left() - 44, plot.bottom()), "0")
        painter.drawText(QPointF(plot.right() + 8, plot.bottom()), "0")

    def _draw_eta_series(
        self,
        painter: QPainter,
        plot: QRectF,
        start_time: datetime,
        duration: float,
        eta_max: float,
    ) -> None:
        points = [
            QPointF(
                _x_for_time(point.timestamp, start_time, duration, plot),
                _y_for_value(point.remaining_seconds, eta_max, plot),
            )
            for point in self._eta_points
        ]
        self._draw_polyline_or_points(painter, points, QColor("#2563eb"), 2.5)

    def _draw_speed_series(
        self,
        painter: QPainter,
        plot: QRectF,
        start_time: datetime,
        duration: float,
        speed_max: float,
    ) -> None:
        points = [
            QPointF(
                _x_for_time(point.timestamp, start_time, duration, plot),
                _y_for_value(point.speed_mps, speed_max, plot),
            )
            for point in self._speed_points
        ]
        self._draw_polyline_or_points(painter, points, QColor("#16a34a"), 2.0)

    def _draw_polyline_or_points(
        self,
        painter: QPainter,
        points: list[QPointF],
        color: QColor,
        width: float,
    ) -> None:
        if not points:
            return
        painter.setPen(QPen(color, width))
        if len(points) > 1:
            for index in range(1, len(points)):
                painter.drawLine(points[index - 1], points[index])
        painter.setBrush(color)
        for point in points:
            painter.drawEllipse(point, 3.2, 3.2)

    def _draw_current_cursor(
        self,
        painter: QPainter,
        plot: QRectF,
        start_time: datetime,
        duration: float,
    ) -> None:
        if self._current_time is None:
            return
        x = _x_for_time(self._current_time, start_time, duration, plot)
        painter.setPen(QPen(QColor("#10233f"), 2))
        painter.drawLine(QPointF(x, plot.top()), QPointF(x, plot.bottom()))
        painter.setFont(QFont("Segoe UI", 8, QFont.Weight.DemiBold))
        painter.drawText(QPointF(x + 5, plot.bottom() - 6), "Jetzt")

    def _draw_legend(self, painter: QPainter, plot: QRectF) -> None:
        entries = [
            ("ETA Restzeit", QColor("#2563eb")),
            ("Geschwindigkeit", QColor("#16a34a")),
            ("SRM/SREM", QColor("#2563eb")),
            ("SSEM Status", QColor("#f59e0b")),
        ]
        x = plot.left()
        y = 18
        painter.setFont(QFont("Segoe UI", 8))
        for label, color in entries:
            painter.setPen(QPen(color, 3))
            painter.drawLine(QPointF(x, y - 4), QPointF(x + 18, y - 4))
            painter.setPen(QPen(QColor("#42546b")))
            painter.drawText(QPointF(x + 24, y), label)
            x += 122


def _x_for_time(timestamp: datetime, start_time: datetime, duration: float, plot: QRectF) -> float:
    offset = max(0.0, min(duration, (timestamp - start_time).total_seconds()))
    return plot.left() + (plot.width() * offset / duration)


def _y_for_value(value: float, maximum: float, plot: QRectF) -> float:
    normalized = max(0.0, min(1.0, value / max(1.0, maximum)))
    return plot.bottom() - (plot.height() * normalized)


def _request_label(kind: str, request_id: Optional[int], sequence_number: Optional[int]) -> str:
    if request_id is None or sequence_number is None:
        return kind
    return f"{kind} {request_id}/{sequence_number}"


def _coerce_int(value: object) -> Optional[int]:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    if isinstance(value, dict):
        for key in ("id", "value", "requestId", "sequenceNumber"):
            coerced = _coerce_int(value.get(key))
            if coerced is not None:
                return coerced
    return None


def _coerce_eta_datetime(value: object, reference_time: datetime) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value
    if not isinstance(value, dict):
        return None
    second_of_minute = _first_number(
        value.get("second"),
        value.get("timeStamp"),
        value.get("millisecond"),
    )
    if second_of_minute is None:
        return None
    if second_of_minute > 60:
        second_of_minute /= 1000.0
    base = reference_time.astimezone(timezone.utc).replace(second=0, microsecond=0)
    candidate = base + timedelta(seconds=second_of_minute)
    if candidate < reference_time - timedelta(seconds=30):
        candidate += timedelta(minutes=1)
    return candidate


def _first_number(*values: object) -> Optional[float]:
    for value in values:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                continue
    return None


def _status_color(status: str) -> QColor:
    token = status.lower()
    if any(keyword in token for keyword in ("grant", "green", "allow", "served")):
        return QColor("#16a34a")
    if any(keyword in token for keyword in ("reject", "deny", "cancel", "terminated")):
        return QColor("#dc2626")
    if any(keyword in token for keyword in ("ack", "process", "receive", "watch", "accept")):
        return QColor("#eab308")
    return QColor("#f59e0b")
