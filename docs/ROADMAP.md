# PCAP2KML Player — Aktualisierte Roadmap

**Stand:** 2026-04-25 | **Version:** 1.7.0+

---

## Phase 1: Stabilisierung & Testing (ABGESCHLOSSEN)

- [x] Test-Suite mit pytest
- [x] Unit- und Integrationstests für Kernmodule
- [x] Globales Exception-Handling
- [x] ASN.1-Decoding-Fehler-Logging
- [x] Parser-Robustheit (Timeout, pyshark, GeoNetworking)
- [x] Drag & Drop, Letzte Sitzung, UX-Auffrischung

---

## Phase 2: ASN.1-Decoding-Verbesserung (ABGESCHLOSSEN)

- [x] Erweiterte Nachrichtenfelder (CAM, DENM, MAPEM, SPATEM, SREM/SSEM)
- [x] Schema-Management (Download, Integritätsprüfung, Fallback)
- [x] Performance: Lazy-Compiling, Cache

---

## Phase 2.5: PKI-Signatur-Analyse (TEILWEISE)

- [x] **A1 — Parser-Vervollständigung**: `assurance_level`, `station_type`, `validity`, `region`, `ITS-AID`
- [x] **A2 — UI-Platzhalter**: "Signatur prüfen"-Button mit Hinweisdialog
- [x] **A3 — ECDSA-Verifikation**: Standalone-Skript (`scripts/verify_ecdsa.py`), opt-in via `cryptography`
- [ ] Zertifikatsketten vollständig parsen (erfordert echte ASN.1/UPER-Decodierung)
- [ ] Signaturverifikation in Haupt-App integrieren

**Anmerkung**: Echte kryptografische Verifikation ist auf explizite **Benutzeranfrage** beschränkt (Sicherheits-/Compliance-Anforderungen).

---

## Phase 2.6: Szenen-Aggregation & Phasenprognose (TEILWEISE)

- [x] Szenen-Datenmodell (IntersectionState, SignalGroupState, SpatForecast)
- [x] MAP-zu-SPaT-Join
- [x] SREM-zu-SSEM-Korrelation
- [x] Timeout-Detektor, Uhrenversatz-Check, ETA-Verifikation
- [x] **Flow-Freigabe-Check**: Lane-Connectivity + `resolve_flow_status()`
- [x] Phasenprognose-Panel (aktueller Stand)
- [ ] Segmentliste für die nächsten 30 s je SignalGroup (vollständige Segmentierung)

---

## Phase 3: Karten- und Visualisierung (TEILWEISE)

### Bereits implementiert
- [x] **Export-Formate**: GeoJSON, CSV, GPX, KML Tour
- [x] **Statistik-Dashboard**: Eigenständiger Dialog mit Nachrichtenraten, Speed/Heading
- [x] **JS-Escaping**: Sicherheit gegen Script-Injection

### Stubs / Vorbereitet
- [ ] Offline-Kartenunterstützung (Vector-Tiles / MapLibre)
- [ ] Heatmap-Overlay + Cluster-Ansicht
- [ ] Koordinaten- und Maßstabsanzeige
- [ ] Screenshot-Export
- [ ] Dichte-Timeline + Loop-Modus + Lesezeichen + Frame-Navigation

**Nächste Schritte**: MapLibre-Integration für Offline-Vector-Tiles (MBTiles / PMTiles), dann Heatmap/Cluster als MapLibre-Layer.

---

## Phase 4: Analyse und Export (TEILWEISE)

- [x] KML-Export (bestehend)
- [x] **GeoJSON-Export** (neu)
- [x] **CSV-Export** (neu)
- [x] **GPX-Export** (neu)
- [x] **Zeitanimierte KML-Tour** (neu)
- [x] **Statistik-Dashboard** (neu)
- [ ] Statistik-Dashboard: Diagramme/Charts (Matplotlib / PyQtGraph)
- [ ] Geschwindigkeits-/Heading-Verteilung als Histogramm

---

## Phase 5: Architektur und Verteilung (IN ARBEIT)

- [x] **pyproject.toml** mit ruff, mypy, pytest, Coverage
- [x] **GitHub Actions CI** (Windows)
- [x] **Lokales CI-Skript** (`scripts/run_ci.ps1`)
- [ ] Type-Checking: 100% mypy-clean (derzeit teilweise ignoriert für Qt-Overrides)
- [ ] Pre-commit-Hooks
- [ ] PyInstaller-Bundle für Windows
- [ ] Headless-Kommandozeilenmodus

---

## Phase 6: Test-Strategie & Qualitätssicherung (ABGESCHLOSSEN)

- [x] **Teststrategie** (`tests/TESTING_STRATEGY.md`) — Pyramide, Risikomatrix, Marks
- [x] **Fixture-Hierarchie** (`tests/conftest.py`, `factories.py`, `conftest_pcap.py`)
- [x] **Coverage-Gate** 80% — aktuell 80.2% Line (306/306 Tests passing)
- [x] **pytest-Marks**: unit, integration, gui, e2e, property, slow, benchmark, pcap_real
- [x] **Unit-Test-Erweiterung**: 39 neue Tests (security_parser, player_controller, map_backend)
- [x] **Bugfixes**: Race-Condition in `_cleanup_loader`, Exception-Handler robust für headless
- [ ] 90% Branch Coverage (aktuell ~65%; erfordert 200+ Parser/Scene-Tests)
- [ ] Property-Tests (Hypothesis — malformed ASN.1/NMEA Frames)
- [ ] GUI-Tests mit pytest-qt (headless `QT_QPA_PLATFORM=offscreen`)

---

## Zusammenfassung der Änderungen

| Branch | Inhalt | Tests |
|--------|--------|-------|
| `bugfix/optimization-round` | Thread-Safety, Signal-Leaks, Timer-Lifecycle, Performance | 245/245 |
| `feature/ci-toolchain` | ruff, mypy, GitHub Actions CI | 254/254 |
| `feature/scene-aggregation-flow` | Lane-Connectivity, Flow-Freigabe-Check | 254/254 |
| `feature/pki-verification` | PKI-Parser, UI-Platzhalter, ECDSA-Skript | 254/254 |
| `feature/phase-d-visualization` | Dashboard, Export-Formate (GeoJSON/CSV/GPX/KML) | 267/267 |
| `feature/testing-strategy` | Teststrategie, Fixtures, 39 neue Tests | 306/306 |

**Gesamt auf `master`: 306 Tests, 80.2% Coverage, 25.7s Laufzeit**

---

- **MapLibre-Integration**: Erfordert WebEngine- oder Qt-Widget-Backend für Vektor-Tiles.
- **Offline-Karten**: MBTiles oder PMTiles als Assets einbinden.
- **Diagramme**: Matplotlib oder PyQtGraph als optionale Dependency.
- **PKI-Integration**: Echte ECDSA-Verifikation nur auf explizite Anfrage.

---

## Empfohlene Nächste Schritte (nach Priorität)

1. **MapLibre-Integration** (Phase 3) — höchste Priorität für Offline-Karten
2. **Diagramme im Dashboard** (Phase 4) — Matplotlib/PyQtGraph für visuelle Statistiken
3. **Pre-commit-Hooks** (Phase 5) — Automatische Formatierung vor Commit
4. **PyInstaller-Bundle** (Phase 5) — Verteilungsfertige Windows-Exe

---

*Letzte Aktualisierung: 2026-04-25*
