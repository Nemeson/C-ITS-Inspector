# PCAP2KML Player — Teststrategie

**Version:** 1.0  
**Datum:** 2026-04-25  
**Autor:** Senior Test Engineer  
**Scope:** Vollständige Test-Pyramide für PCAP2KML Player (PyQt6, V2X/ITS, Windows)

---

## 1. Ziele & Kennzahlen

| Kennzahl | Ziel | Aktuell (Stand 2026-04-25) |
|----------|------|----------------------------|
| Line Coverage | ≥ 90 % | 78.0 % |
| Branch Coverage | ≥ 90 % | ~70 % (geschätzt) |
| Testanzahl Unit | ≥ 400 | 267 |
| Testanzahl Integration | ≥ 30 | 0 |
| Testanzahl Property | ≥ 20 | 0 |
| Testanzahl GUI | ≥ 15 | 0 |
| Testanzahl Benchmark | ≥ 10 | 0 |
| Testlaufzeit (ohne slow/benchmark) | < 60 s | 24 s |
| Testlaufzeit (vollständig) | < 10 min | — |

---

## 2. Test-Pyramide (ASCII)

```
         /\
        /  \   E2E / GUI (5%)
       /----\
      /      \  Integration (15%)
     /--------\
    /          \ Property / Benchmark (10%)
   /------------\
  /              \ Unit (70%)
 /----------------\
```

| Ebene | Anteil | Werkzeuge | Scope |
|-------|--------|-----------|-------|
| **Unit** | 70% | pytest, Fakes, Builder | Funktionen, Klassen, State-Maschinen |
| **Property** | 10% | hypothesis, pytest | Parser-Robustheit, DTO-Invarianten |
| **Integration** | 15% | pytest, echte Dateien | TXA+RXA-Merge, Scene-Pipeline, Export |
| **E2E / GUI** | 5% | pytest-qt, offscreen | MainWindow-Interaktion, Drag&Drop |

---

## 3. Risiko-Priorisierungsmatrix

| Modul | Lines | Branch % | Risiko | Priorität | Lücken |
|-------|-------|----------|--------|-----------|--------|
| `security_parser.py` | 231 | ~45 | **KRITISCH** | 1 | Zertifikats-Scanner, Heuristik-Felder |
| `player_controller.py` | 171 | ~55 | **KRITISCH** | 1 | Scrubbing, Speed, State-Transition |
| `pcap_parser.py` | 770 | ~65 | **HOCH** | 2 | GeoNetworking, pyshark-Timeout, MAP |
| `map_backend.py` | 24 | ~50 | **HOCH** | 2 | Env-Fallbacks |
| `asn1_schemas.py` | 209 | ~60 | **MITTEL** | 3 | Git-Clone, Kompilierung |
| `scene_model.py` | 759 | ~75 | **MITTEL** | 3 | Phasenprognose, ETA |
| `merge_model.py` | 194 | ~75 | **MITTEL** | 4 | Merge-Gruppen |
| `nmea_parser.py` | 95 | ~75 | **NIEDRIG** | 4 | RMC/GGA |

### Coverage-Ziel pro Modul

| Modul | Line-Ziel | Branch-Ziel | Schwerpunkt |
|-------|-----------|-------------|-------------|
| security_parser.py | 95% | 90% | `_scan_assurance`, `_scan_station_type`, `_scan_validity` |
| player_controller.py | 95% | 90% | `jump_to_next_issue`, `set_speed`, `toggle_play` |
| pcap_parser.py | 90% | 85% | `parse_pcap`, `_normalize_map_connection`, `geolocate` |
| map_backend.py | 95% | 100% | `MAP_PERFORMANCE_*` |
| asn1_schemas.py | 90% | 85% | `update_from_git`, `compile_schemas` |
| scene_model.py | 90% | 85% | `build_scene_snapshot`, `_extract_phase_segments` |
| merge_model.py | 90% | 85% | `build_merge_groups` |
| nmea_parser.py | 95% | 90% | `parse_nmea_sentence` |
| data_model.py | 98% | 95% | (bereits gut abgedeckt) |
| statistics.py | 98% | 95% | (bereits gut abgedeckt) |
| export_formats.py | 98% | 95% | (bereits gut abgedeckt) |

---

## 4. Test-Kategorien & pytest-Marks

```python
# Registriert in pyproject.toml unter [tool.pytest.ini_options]
markers = [
    "unit: Fast isolated unit tests (default)",
    "integration: Module interactions and real files",
    "gui: PyQt6 widget tests (requires pytest-qt)",
    "e2e: End-to-end full pipeline (slow)",
    "property: Hypothesis property-based tests",
    "slow: Tests > 5 s (real PCAP, benchmark)",
    "benchmark: pytest-benchmark performance tests",
    "pcap_real: Tests requiring real capture files",
    "network: Tests requiring network (mocked by default)",
    "qt_headless: Requires QT_QPA_PLATFORM=offscreen",
]
```

### Ausführungskommandos

```bash
# Default: nur Unit-Tests (schnell)
pytest -m "unit and not slow"

# Mit Coverage (Ziel: 90%)
pytest --cov=pcap2kml_player --cov-branch --cov-fail-under=90 --cov-report=term-missing

# GUI-Tests (headless)
set QT_QPA_PLATFORM=offscreen
pytest -m gui

# Integration + Property
pytest -m "integration or property"

# Alle außer slow/benchmark (Schnelllauf, Ziel < 60 s)
pytest -m "not slow and not benchmark"

# Vollständiger Lauf (alle Tests, Ziel < 10 min)
pytest --cov=pcap2kml_player --cov-branch --cov-report=html

# Parallele Ausführung
pytest -n auto -m "not gui and not benchmark"

# Nur Benchmarks
pytest -m benchmark --benchmark-only

# Echte PCAP-Dateien
pytest -m pcap_real --testfiles=./testfiles
```

---

## 5. Fixture-Hierarchie

### Session-Scope (`tests/conftest.py`)

| Fixture | Scope | Zweck |
|---------|-------|-------|
| `qapp` | session | Qt Application (headless) |
| `qtbot` | function | QtBot für GUI-Interaktion |
| `tmp_pcap` | session | Temporäre PCAP-Kopien |
| `synthetic_session` | function | SessionData mit Builder |
| `frozen_time` | function | Deterministische Zeit (freezegun) |
| `disable_webengine` | session | Native statt WebEngine |

### Module-Scope

| Fixture | Modul | Zweck |
|---------|-------|-------|
| `fake_table` | test_ui_helpers | QTableWidget-Double |
| `fake_viewport` | test_map_widget | Fake-Map-Viewport |
| `scapy_session` | test_property_pcap_parser | Deterministische PCAP-Frames |

### Function-Scope

| Fixture | Zweck |
|---------|-------|
| `sample_cam_msg` | Einzelne CAM-Nachricht |
| `sample_denm_msg` | Einzelne DENM-Nachricht |
| `sample_map_msg` | MAPEM mit LaneSet |
| `sample_spat_msg` | SPATEM mit SignalGroups |
| `sample_srem_msg` | SREM mit Request |
| `sample_ssem_msg` | SSEM mit Response |

---

## 6. Fake-vs-Mock-Doctrine

### Regel: **Fake > Mock**

| Pattern | Wann | Beispiel |
|---------|------|----------|
| **Fake** | State-basierte Logik, wiederholbar | `FakeTable` statt `QTableWidget`, `FakeSession` statt `SessionData` |
| **Stub** | Einfache Antwort ohne Logik | `FakeWebEngine` gibt fixe HTML-Responses |
| **Spy** | Verifikation von Aufrufen | `FakeMapWidget` zählt `applyPayload`-Aufrufe |
| **Mock** | Nur wenn Interface extern/unzugänglich | `monkeypatch` für `subprocess.run` |

### Verboten
- `unittest.mock.patch` in Unit-Tests → Fakes verwenden
- `autospec=True` ohne Notwendigkeit → Fake implementieren
- `side_effect`-Ketten → Echte State-Maschinen bauen

---

## 7. Synthetische PCAP-Generierung

### Ziel
Deterministische, reproduzierbare Testdaten ohne echte Captures.

### Technik (`tests/conftest_pcap.py`)
```python
# scapy-basierte Generierung
from scapy.layers.l2 import Ether
from scapy.layers.inet import UDP
from scapy.packet import Raw

def make_cam_pcap(bytes_payload: bytes) -> list[bytes]:
    """GeoNetworking + BTP-B + ITS-PDU-Header + CAM-Payload."""
    # ...
```

### Varianten pro Typ
- **CAM**: Variationen für vehicleWidth, driveDirection, stationType
- **DENM**: Variationen für causeCode, subCauseCode, severity
- **MAPEM**: Variationen für laneSet (Inbound/Outbound, connectsTo)
- **SPATEM**: Variationen für signalGroups (MovementState, Timing)
- **SREM**: Variationen für requestorRole, sequenceNumber, eta
- **SSEM**: Variationen für status, sequenceNumber

### Corruption-Mutationen (für Property-Tests)
- Truncation (letzte N Bytes entfernt)
- Wrong EtherType (0x88B5 statt 0x88B6)
- Invalid ASN.1 length fields
- Wrong checksums
- Malformed NMEA-GGA ($GPGGA mit fehlenden Feldern)

---

## 8. Property-Based Testing

### Bereiche

| Modul | Eigenschaft | Hypothesis-Strategie |
|-------|-------------|----------------------|
| `pcap_parser` | Crasht nie bei malformed Frames | `st.binary(min_size=10, max_size=2048)` |
| `pcap_parser` | Ignoriert unbekannte EtherTypes | `st.sampled_from([0x88B5, 0x0800, 0x86DD])` |
| `nmea_parser` | Parst immer gültige GGA/RMC | `st.text(alphabet='0123456789,.NSEW', min_size=20)` |
| `data_model` | Round-Trip JSON-Serialisierung | `st.builds(V2xMessage, ...)` |
| `security_parser` | Heuristik gibt None statt Exception | `st.binary(min_size=2, max_size=512)` |
| `merge_model` | Merge ist kommutativ + assoziativ | `st.lists(st.builds(V2xMessage,...), min_size=2)` |

---

## 9. GUI-Test-Strategie

### Headless-Ausführung
```bash
set QT_QPA_PLATFORM=offscreen
set QT_OPENGL=software
pytest -m gui
```

### Pytest-qt Patterns
```python
def test_map_widget_click_shows_popup(qtbot, fake_map):
    qtbot.mouseClick(fake_map, Qt.MouseButton.LeftButton)
    assert fake_map._last_clicked_msg is not None
```

### Was getestet wird
- `MainWindow`-Lifecycle (show/hide/close)
- Toolbar-Button-Callbacks
- Filter-Checkboxen (State-Änderung → Tabelle aktualisiert)
- Slider-Scrubbing (Zeitleiste → Player-Position)
- Drag&Drop (QEvent-Mock oder echte Qt-Events)
- Tab-Wechsel (Details ↔ Szene ↔ ETA)

### Was NICHT getestet wird
- WebEngine-Rendering (zu instabil, zu langsam)
- OpenGL/Canvas-Leinwand
- Font-Rendering

---

## 10. Performance-Budgets

### Parse-Throughput
```python
def test_parse_throughput(benchmark, tmp_path):
    pcap = make_synthetic_pcap(1000, MessageType.CAM)
    result = benchmark(parse_pcap, str(pcap), SessionData())
    assert result > 50  # msgs/s Minimum
```

### Render-Latenz
```python
def test_render_payload_latency(benchmark, map_widget):
    payload = make_large_payload(1000)
    benchmark(map_widget.apply_render_payload, payload)
    # Ziel: < 100 ms für 1000 Marker
```

### RAM-Wächter
```python
def test_ram_watcher_triggers_saver_at_80_percent(mocker):
    mocker.patch('psutil.Process.memory_percent', return_value=82.0)
    watcher = RamWatcher(threshold=80)
    watcher.check()
    assert watcher.mode == PerformanceMode.SAVER
```

---

## 11. Coverage-Gate

In `pyproject.toml`:
```toml
[tool.coverage.run]
branch = true
source = ["pcap2kml_player"]
omit = [
    "pcap2kml_player/main.py",
    "pcap2kml_player/ui/*",
    "pcap2kml_player/map_widget.py",
]

[tool.coverage.report]
precision = 1
fail_under = 90
show_missing = true
skip_covered = false
```

### Coverage-Ausnahmen (erlaubt)
| Modul | Grund | Max. Lücke |
|-------|-------|------------|
| `main.py` | Entrypoint, Qt-Init | 100% OK |
| `ui/main_window.py` | GUI, Qt-Events | 50% OK |
| `map_widget.py` | WebEngine-JS | 50% OK |

---

## 12. Test-Dateien-Struktur

```
tests/
├── TESTING_STRATEGY.md      # Dieses Dokument
├── conftest.py              # Globale Fixtures
├── conftest_pcap.py         # PCAP-Generierung
├── factories.py             # V2xMessage-Builder
├── fakes/
│   ├── __init__.py
│   ├── fake_qt.py           # QTableWidget, FakeQTimer
│   ├── fake_map.py          # FakeWebEngine, FakeMapWidget
│   └── fake_player.py       # FakePlayerController
├── test_*.py                 # Bestehende + Neue
```

---

## 13. Refactoring-Roadmap der bestehenden Tests

### Schritt 1: Factory-Pattern für V2xMessage
```python
# Alt (in 8 Dateien kopiert):
def _make_msg(**kwargs):
    defaults = {...}
    defaults.update(kwargs)
    return V2xMessage(**defaults)

# Neu (in factories.py):
from tests.factories import V2xMessageBuilder
msg = V2xMessageBuilder().cam().with_speed(50).with_coordinates(52,13).build()
```

### Schritt 2: Fake-Konsolidierung
- `FakeTable`, `FakeViewport`, `FakeWebEngine`, `FakeQTimer`
- Entfernen aller Inline-Mocks (`type("Signal", ...)`)

### Schritt 3: Parametrisierung
```python
@pytest.mark.parametrize("perf_mode", ["normal", "saver", "diagnostic"])
def test_render_payload_respects_budget(perf_mode):
    ...
```

---

## 14. Checkliste: Implementierungs-Vorgehen

- [ ] **Schritt 1**: Inventur (Coverage-Messung) ✅
- [ ] **Schritt 2**: TESTING_STRATEGY.md schreiben ✅
- [ ] **Schritt 3**: pyproject.toml erweitern (Marks, Coverage-Gate)
- [ ] **Schritt 4**: tests/conftest.py + conftest_pcap.py
- [ ] **Schritt 5**: tests/factories.py + tests/fakes/
- [ ] **Schritt 6**: Neue Testdateien (Unit → Property → Integration → E2E → GUI → Benchmark)
- [ ] **Schritt 7**: Refactoring bestehender Tests
- [ ] **Schritt 8**: Coverage-Lückenschluss-Iteration
- [ ] **Schritt 9**: Finale Verifikation (Alle Tests grün, ≥ 90% Branch)

---

*Letzte Aktualisierung: 2026-04-25*
