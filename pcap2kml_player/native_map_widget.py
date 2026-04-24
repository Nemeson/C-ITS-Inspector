"""Qt-native fallback map for systems where QtWebEngine cannot create GL contexts."""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from math import cos, radians
from typing import Optional

from PyQt6.QtCore import QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QGraphicsEllipseItem, QGraphicsPathItem, QGraphicsRectItem, QGraphicsScene, QGraphicsTextItem, QGraphicsView

from .data_model import MessageType, V2xMessage
from .map_backend import (
    MAP_PERFORMANCE_DIAGNOSTIC,
    MAP_PERFORMANCE_MODES,
    MAP_PERFORMANCE_NORMAL,
    MAP_PERFORMANCE_SAVER,
)

PLAYBACK_TRAIL_POINTS = 8
STATION_PALETTE = [
    "#e6194b",
    "#3cb44b",
    "#4363d8",
    "#f58231",
    "#911eb4",
    "#42d4f4",
    "#f032e6",
    "#bfef45",
    "#fabed4",
    "#469990",
]
INFRASTRUCTURE_MESSAGE_COLORS = {
    MessageType.MAPEM: "#1f9d55",
    MessageType.SPATEM: "#c026d3",
}
NON_STATION_MARKER_TYPES = {
    MessageType.MAPEM,
    MessageType.SPATEM,
    MessageType.SSEM,
}


@dataclass(frozen=True)
class NativeMapTelemetry:
    """Compact diagnostics with the same keys as the WebEngine map telemetry."""

    timestamp: float
    performance_mode: str
    source_message_count: int
    visible_message_count: int
    marker_count: int
    infrastructure_count: int
    trajectory_count: int
    trajectory_point_count: int
    payload_bytes: int = 0
    queued_payload_replaced: bool = False
    budget_dropped_markers: int = 0
    budget_dropped_infrastructure: int = 0
    budget_dropped_trajectories: int = 0
    budget_dropped_trajectory_points: int = 0

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class NativeMapWidget(QGraphicsView):
    """A lightweight local map that avoids QtWebEngine and GPU compositing."""

    telemetry_updated = pyqtSignal(dict)
    map_issue_detected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setBackgroundBrush(QColor("#eef4fb"))
        self._station_color_map: dict[str, str] = {}
        self._station_index = 0
        self._performance_mode = MAP_PERFORMANCE_NORMAL
        self._latest_telemetry: Optional[NativeMapTelemetry] = None
        self._last_messages: list[V2xMessage] = []
        self._highlighted_request: Optional[tuple[int, int, int]] = None
        self._focused_intersection: Optional[int] = None
        self.setMinimumSize(200, 150)
        self._draw_ready_hint()

    def set_performance_mode(self, mode: str) -> None:
        if mode not in MAP_PERFORMANCE_MODES:
            mode = MAP_PERFORMANCE_NORMAL
        self._performance_mode = mode
        if self._last_messages:
            self.load_messages(self._last_messages)

    def latest_telemetry(self) -> Optional[dict[str, object]]:
        if self._latest_telemetry is None:
            return None
        return self._latest_telemetry.to_dict()

    def reload_map_page(self) -> None:
        self.load_messages(self._last_messages)

    def load_messages(self, messages: list[V2xMessage]) -> None:
        self._last_messages = list(messages)
        self._render_messages(messages, max_index=None, fit_view=True, short_trails=False)

    def render_playback_slice(
        self,
        messages: list[V2xMessage],
        current_index: int,
        *,
        window_seconds: Optional[float] = None,
    ) -> None:
        if not messages:
            self.clear()
            return
        safe_index = max(0, min(current_index, len(messages) - 1))
        window_start = None
        if window_seconds is not None and window_seconds > 0:
            window_start = messages[safe_index].timestamp.timestamp() - window_seconds
        self._render_messages(
            messages,
            max_index=safe_index,
            window_start_timestamp=window_start,
            fit_view=False,
            short_trails=True,
        )

    def update_playback_position(self, msg: V2xMessage) -> None:
        if not self._last_messages:
            self.load_messages([msg])

    def highlight_request(self, intersection_id: int, request_id: int, sequence_number: int) -> None:
        self._highlighted_request = (intersection_id, request_id, sequence_number)
        if self._last_messages:
            self.load_messages(self._last_messages)

    def focus_intersection(self, intersection_id: int) -> None:
        self._focused_intersection = intersection_id

    def clear(self) -> None:
        self._scene.clear()
        self._station_color_map.clear()
        self._station_index = 0
        self._last_messages = []
        self._record_telemetry(
            NativeMapTelemetry(
                timestamp=time.time(),
                performance_mode=self._performance_mode,
                source_message_count=0,
                visible_message_count=0,
                marker_count=0,
                infrastructure_count=0,
                trajectory_count=0,
                trajectory_point_count=0,
            )
        )

    def wheelEvent(self, event) -> None:
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)

    def _render_messages(
        self,
        messages: list[V2xMessage],
        *,
        max_index: Optional[int],
        window_start_timestamp: Optional[float] = None,
        fit_view: bool,
        short_trails: bool,
    ) -> None:
        self._scene.clear()
        end_index = len(messages) if max_index is None else min(max_index + 1, len(messages))
        visible = [
            msg
            for msg in messages[:end_index]
            if _has_display_position(msg)
            and (
                window_start_timestamp is None
                or msg.timestamp.timestamp() >= window_start_timestamp
                or msg.msg_type in INFRASTRUCTURE_MESSAGE_COLORS
            )
        ]
        bounds = _bounds_for_messages(visible)
        if bounds is None:
            self._draw_empty_hint()
            self._record_telemetry(
                NativeMapTelemetry(
                    timestamp=time.time(),
                    performance_mode=self._performance_mode,
                    source_message_count=end_index,
                    visible_message_count=0,
                    marker_count=0,
                    infrastructure_count=0,
                    trajectory_count=0,
                    trajectory_point_count=0,
                )
            )
            return

        projected = [_project_message(msg, bounds) for msg in visible]
        station_coords: dict[str, list[tuple[float, float]]] = {}
        latest_station_points: dict[str, tuple[V2xMessage, tuple[float, float]]] = {}
        infrastructure_count = 0
        for msg, point in projected:
            if msg.msg_type in INFRASTRUCTURE_MESSAGE_COLORS:
                self._draw_infrastructure(msg, point)
                infrastructure_count += 1
                continue
            if msg.msg_type in NON_STATION_MARKER_TYPES:
                continue
            station_coords.setdefault(msg.station_id, []).append(point)
            latest_station_points[msg.station_id] = (msg, point)

        trajectory_count = 0
        trajectory_point_count = 0
        if self._performance_mode != MAP_PERFORMANCE_DIAGNOSTIC:
            for station_id, coords in station_coords.items():
                if short_trails:
                    coords = coords[-PLAYBACK_TRAIL_POINTS:]
                if self._performance_mode == MAP_PERFORMANCE_SAVER and len(station_coords) > 25:
                    continue
                self._draw_trajectory(coords, self._station_color(station_id))
                trajectory_count += 1
                trajectory_point_count += len(coords)

        for station_id, (msg, point) in latest_station_points.items():
            self._draw_marker(msg, point, self._station_color(station_id))

        self._scene.setSceneRect(self._scene.itemsBoundingRect().adjusted(-60, -60, 60, 60))
        if fit_view:
            self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self._record_telemetry(
            NativeMapTelemetry(
                timestamp=time.time(),
                performance_mode=self._performance_mode,
                source_message_count=end_index,
                visible_message_count=len(visible),
                marker_count=len(latest_station_points),
                infrastructure_count=infrastructure_count,
                trajectory_count=trajectory_count,
                trajectory_point_count=trajectory_point_count,
            )
        )

    def _draw_empty_hint(self) -> None:
        text = QGraphicsTextItem("Keine gueltigen Kartenpositionen verfuegbar")
        text.setDefaultTextColor(QColor("#42546b"))
        text.setPos(20, 20)
        self._scene.addItem(text)

    def _draw_ready_hint(self) -> None:
        bg = QGraphicsRectItem(QRectF(0, 0, 420, 80))
        bg.setBrush(QColor("#d0e8f7"))
        bg.setPen(QPen(QColor("#90bcd8"), 1.0))
        self._scene.addItem(bg)

        title = QGraphicsTextItem("Qt-Native Kartenansicht")
        title.setDefaultTextColor(QColor("#1e3a5f"))
        title.setPos(14, 8)
        self._scene.addItem(title)

        hint = QGraphicsTextItem("Leaflet/WebEngine nicht verfügbar — PCAP laden, um Nachrichten anzuzeigen")
        hint.setDefaultTextColor(QColor("#42546b"))
        hint.setPos(14, 36)
        self._scene.addItem(hint)

        self._scene.setSceneRect(QRectF(0, 0, 420, 160))

    def _draw_marker(self, msg: V2xMessage, point: tuple[float, float], color: str) -> None:
        radius = 7.0
        item = QGraphicsEllipseItem(point[0] - radius, point[1] - radius, radius * 2, radius * 2)
        item.setBrush(QColor(color))
        item.setPen(QPen(QColor("#10233f"), 1.5))
        item.setToolTip(
            f"{msg.msg_type.value}\nStation: {msg.station_id}\n"
            f"Zeit: {msg.timestamp.strftime('%H:%M:%S.%f')[:-3]}\n"
            f"Position: {msg.latitude:.6f}, {msg.longitude:.6f}"
        )
        self._scene.addItem(item)

    def _draw_infrastructure(self, msg: V2xMessage, point: tuple[float, float]) -> None:
        radius = 11.0
        color = INFRASTRUCTURE_MESSAGE_COLORS.get(msg.msg_type, "#475569")
        item = QGraphicsEllipseItem(point[0] - radius, point[1] - radius, radius * 2, radius * 2)
        item.setBrush(QColor(color))
        item.setPen(QPen(QColor("#ffffff"), 2.0))
        item.setToolTip(f"{msg.msg_type.value}\nStation: {msg.station_id}")
        self._scene.addItem(item)
        label = QGraphicsTextItem(msg.msg_type.value)
        label.setDefaultTextColor(QColor("#10233f"))
        label.setPos(point[0] + 12, point[1] - 12)
        self._scene.addItem(label)

    def _draw_trajectory(self, coords: list[tuple[float, float]], color: str) -> None:
        if len(coords) < 2:
            return
        path = QPainterPath()
        path.moveTo(*coords[0])
        for point in coords[1:]:
            path.lineTo(*point)
        item = QGraphicsPathItem(path)
        item.setPen(QPen(QColor(color), 2.0, Qt.PenStyle.SolidLine))
        item.setOpacity(0.65)
        self._scene.addItem(item)

    def _station_color(self, station_id: str) -> str:
        if station_id not in self._station_color_map:
            self._station_color_map[station_id] = STATION_PALETTE[
                self._station_index % len(STATION_PALETTE)
            ]
            self._station_index += 1
        return self._station_color_map[station_id]

    def _record_telemetry(self, telemetry: NativeMapTelemetry) -> None:
        self._latest_telemetry = telemetry
        self.telemetry_updated.emit(telemetry.to_dict())


def _has_display_position(msg: V2xMessage) -> bool:
    if not (-90 <= msg.latitude <= 90 and -180 <= msg.longitude <= 180):
        return False
    return not (abs(msg.latitude) < 1e-9 and abs(msg.longitude) < 1e-9)


def _bounds_for_messages(messages: list[V2xMessage]) -> Optional[tuple[float, float, float, float]]:
    if not messages:
        return None
    lats = [msg.latitude for msg in messages]
    lons = [msg.longitude for msg in messages]
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)
    if abs(max_lat - min_lat) < 1e-9:
        min_lat -= 0.0005
        max_lat += 0.0005
    if abs(max_lon - min_lon) < 1e-9:
        min_lon -= 0.0005
        max_lon += 0.0005
    return (min_lat, max_lat, min_lon, max_lon)


def _project_message(
    msg: V2xMessage,
    bounds: tuple[float, float, float, float],
) -> tuple[V2xMessage, tuple[float, float]]:
    min_lat, max_lat, min_lon, max_lon = bounds
    width = 1200.0
    height = 800.0
    mid_lat = (min_lat + max_lat) / 2.0
    lon_scale = max(0.2, cos(radians(mid_lat)))
    x = ((msg.longitude - min_lon) * lon_scale / max(1e-9, (max_lon - min_lon) * lon_scale)) * width
    y = (1.0 - ((msg.latitude - min_lat) / max(1e-9, max_lat - min_lat))) * height
    return msg, (x, y)
