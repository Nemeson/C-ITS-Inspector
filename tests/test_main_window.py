from __future__ import annotations

from datetime import datetime, timezone

from pcap2kml_player.data_model import MessageType, V2xMessage
from pcap2kml_player.ui.main_window import COL_TIMESTAMP, MainWindow


def _message(second: int, station_id: str = "car-1") -> V2xMessage:
    return V2xMessage(
        timestamp=datetime(2026, 4, 19, 12, 0, second, tzinfo=timezone.utc),
        station_id=station_id,
        msg_type=MessageType.CAM,
        latitude=52.0,
        longitude=13.0,
    )


class _Rect:
    def __init__(self, visible: bool):
        self._visible = visible

    def isValid(self) -> bool:
        return True

    def intersects(self, _other) -> bool:
        return self._visible


class _Viewport:
    def rect(self) -> _Rect:
        return _Rect(True)


class _FakeTable:
    def __init__(self, visible_rows: set[int] | None = None):
        self.visible_rows = visible_rows or set()
        self.selected_rows: list[int] = []
        self.scrolled_rows: list[int] = []
        self._items: dict[tuple[int, int], object] = {}

    def setRowCount(self, _count: int) -> None:
        return None

    def setItem(self, row: int, column: int, item: object) -> None:
        self._items[(row, column)] = item

    def item(self, row: int, column: int) -> object | None:
        return self._items.get((row, column))

    def selectRow(self, row: int) -> None:
        self.selected_rows.append(row)

    def scrollToItem(self, item: object, _hint: object) -> None:
        for (row, _column), candidate in self._items.items():
            if candidate is item:
                self.scrolled_rows.append(row)
                return

    def visualItemRect(self, item: object) -> _Rect:
        for (row, _column), candidate in self._items.items():
            if candidate is item:
                return _Rect(row in self.visible_rows)
        return _Rect(False)

    def viewport(self) -> _Viewport:
        return _Viewport()


class _FakeTabs:
    def __init__(self, index: int = 1):
        self._index = index
        self.visible = True
        self.history: list[int] = []

    def currentIndex(self) -> int:
        return self._index

    def setCurrentIndex(self, index: int) -> None:
        self._index = index
        self.history.append(index)

    def setVisible(self, visible: bool) -> None:
        self.visible = visible


class _FakeButton:
    def __init__(self):
        self.text = ""

    def setText(self, text: str) -> None:
        self.text = text


class _FakeSplitter:
    def __init__(self):
        self.sizes: list[int] = []

    def setSizes(self, sizes: list[int]) -> None:
        self.sizes = sizes


class _FakeDetailTable:
    def __init__(self):
        self.row_count = 0
        self.items: dict[tuple[int, int], object] = {}
        self.visible = False

    def setRowCount(self, count: int) -> None:
        self.row_count = count

    def setItem(self, row: int, column: int, item: object) -> None:
        self.items[(row, column)] = item

    def show(self) -> None:
        self.visible = True


def test_populate_message_table_builds_lookup_without_full_window_init():
    window = MainWindow.__new__(MainWindow)
    window._session = None
    window._message_row_lookup = {}
    window._last_highlighted_row = None
    window._msg_table = _FakeTable()

    first = _message(0, "car-1")
    second = _message(1, "car-2")

    window._populate_message_table([first, second])

    assert window._message_row_lookup[window._message_lookup_key(first)] == 0
    assert window._message_row_lookup[window._message_lookup_key(second)] == 1


def test_highlight_table_row_skips_scroll_when_row_is_already_visible():
    window = MainWindow.__new__(MainWindow)
    msg = _message(0, "car-1")
    key = (msg.timestamp.strftime("%H:%M:%S.%f")[:-3], msg.station_id)
    table = _FakeTable(visible_rows={2})
    timestamp_item = object()
    table.setItem(2, COL_TIMESTAMP, timestamp_item)

    window._msg_table = table
    window._message_row_lookup = {key: 2}
    window._last_highlighted_row = None

    window._highlight_table_row(msg)

    assert table.selected_rows == [2]
    assert table.scrolled_rows == []
    assert window._last_highlighted_row == 2


def test_highlight_table_row_avoids_repeat_selection_for_same_row():
    window = MainWindow.__new__(MainWindow)
    msg = _message(0, "car-1")
    key = (msg.timestamp.strftime("%H:%M:%S.%f")[:-3], msg.station_id)
    table = _FakeTable()
    timestamp_item = object()
    table.setItem(3, COL_TIMESTAMP, timestamp_item)

    window._msg_table = table
    window._message_row_lookup = {key: 3}
    window._last_highlighted_row = 3

    window._highlight_table_row(msg)

    assert table.selected_rows == []
    assert table.scrolled_rows == []


def test_show_security_detail_defers_refresh_when_scene_tab_is_active():
    window = MainWindow.__new__(MainWindow)
    msg = _message(0, "car-1")
    window._context_tabs = _FakeTabs(index=1)
    window._detail_table = _FakeDetailTable()
    window._pending_detail_message = None
    window._last_detail_key = None

    window._show_security_detail(msg, auto_focus=False)

    assert window._pending_detail_message is msg
    assert window._detail_table.row_count == 0
    assert window._last_detail_key is None


def test_on_context_tab_changed_renders_pending_details():
    window = MainWindow.__new__(MainWindow)
    msg = _message(0, "car-1")
    window._context_tabs = _FakeTabs(index=0)
    window._detail_table = _FakeDetailTable()
    window._pending_detail_message = msg
    window._last_detail_key = None

    window._on_context_tab_changed(0)

    assert window._detail_table.row_count > 0
    assert window._last_detail_key == window._message_lookup_key(msg)


def test_toggle_message_table_maximized_hides_context_tabs():
    window = MainWindow.__new__(MainWindow)
    window._context_tabs = _FakeTabs(index=1)
    window._btn_toggle_message_table = _FakeButton()
    window._right_splitter = _FakeSplitter()
    window._message_table_maximized = False

    window._toggle_message_table_maximized(True)
    assert window._message_table_maximized is True
    assert window._context_tabs.visible is False
    assert window._right_splitter.sizes == [1, 0]
    assert window._btn_toggle_message_table.text == "Tabellenbereich wiederherstellen"

    window._toggle_message_table_maximized(False)
    assert window._message_table_maximized is False
    assert window._context_tabs.visible is True
    assert window._right_splitter.sizes == [460, 280]
    assert window._btn_toggle_message_table.text == "Tabelle maximieren"
