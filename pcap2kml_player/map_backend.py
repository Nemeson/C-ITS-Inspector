"""Map backend selection without importing QtWebEngine unless needed."""

from __future__ import annotations

import os

MAP_PERFORMANCE_NORMAL = "normal"
MAP_PERFORMANCE_SAVER = "saver"
MAP_PERFORMANCE_DIAGNOSTIC = "diagnostic"
MAP_PERFORMANCE_MODES = {
    MAP_PERFORMANCE_NORMAL,
    MAP_PERFORMANCE_SAVER,
    MAP_PERFORMANCE_DIAGNOSTIC,
}
MAP_BACKEND_WEBENGINE = "webengine"
MAP_BACKEND_NATIVE = "native"
MAP_BACKEND_AUTO = "auto"
MAP_BACKENDS = {MAP_BACKEND_WEBENGINE, MAP_BACKEND_NATIVE}


def prefer_native_map_backend() -> bool:
    """Return whether the app should use the Qt-native fallback map."""
    configured = os.environ.get("PCAP2KML_MAP_BACKEND", MAP_BACKEND_AUTO).strip().lower()
    if configured == MAP_BACKEND_NATIVE:
        return True
    return False


def selected_map_backend_name() -> str:
    """Return the concrete map backend name selected for this process."""
    return MAP_BACKEND_NATIVE if prefer_native_map_backend() else MAP_BACKEND_WEBENGINE


def create_map_widget(parent=None, backend: str | None = None):
    """Create the selected map widget implementation."""
    selected_backend = (backend or selected_map_backend_name()).strip().lower()
    if selected_backend == MAP_BACKEND_NATIVE:
        from .native_map_widget import NativeMapWidget

        return NativeMapWidget(parent)

    from .map_widget import MapWidget

    return MapWidget(parent)
