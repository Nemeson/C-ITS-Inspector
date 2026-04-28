from __future__ import annotations

from pcap2kml_player.map_backend import (
    MAP_PERFORMANCE_DIAGNOSTIC,
    MAP_PERFORMANCE_MODES,
    MAP_PERFORMANCE_NORMAL,
    MAP_PERFORMANCE_SAVER,
)


def test_performance_mode_constants_are_distinct():
    assert MAP_PERFORMANCE_NORMAL != MAP_PERFORMANCE_SAVER
    assert MAP_PERFORMANCE_SAVER != MAP_PERFORMANCE_DIAGNOSTIC
    assert MAP_PERFORMANCE_NORMAL != MAP_PERFORMANCE_DIAGNOSTIC


def test_performance_modes_set_contains_all_constants():
    assert {
        MAP_PERFORMANCE_NORMAL,
        MAP_PERFORMANCE_SAVER,
        MAP_PERFORMANCE_DIAGNOSTIC,
    } == MAP_PERFORMANCE_MODES
