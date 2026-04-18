# PCAP2KML Player — Roadmap

**Stand:** 2026-04-18 | **Version:** 1.0

---

## Phase 1: Stabilisierung & Testing (v1.1)

### 1.1 Unit- und Integrationstests
- [ ] Test-Suite mit `pytest` aufsetzen (`tests/`-Verzeichnis)
- [ ] `test_data_model.py` — V2xMessage, SessionData, Filterlogik
- [ ] `test_nmea_parser.py` — GPGGA/GPRMC-Parsing mit echten und fehlerhaften Sätzen
- [ ] `test_pcap_parser.py` — Scapy-Backend mit Test-PCAPs
- [ ] `test_kml_exporter.py` — KML-Generierung, Filteroptionen
- [ ] Test-PCAP-Dateien mit bekannten V2X-Nachrichten erstellen/beziehen
- [ ] Ziel: 80%+ Testabdeckung

### 1.2 Fehlerbehandlung & Robustheit
- [ ] Globales Exception-Handling (unhandled exceptions abfangen)
- [ ] Fortschrittsanzeige beim PCAP-Laden (QProgressBar für große Dateien)
- [ ] Abbrechen-Button beim Laden langer PCAPs
- [ ] ASN.1-Decoding-Fehler pro Nachricht loggen statt nur warn
- [ ] Prüfung auf fehlende Abhängigkeiten beim Start (PyQt6, scapy, etc.)

### 1.3 Pyshark-Backend verbessen
- [ ] Timeout-Handling für pyshark.FileCapture
- [ ] Bessere Filterstrategie (BTP-Filter statt generischem "btp or nmea or gps")
- [ ] GeoNetworking-Header-Extraktion (Quell-/Zieladresse)
- [ ] ITS-PDU-Header-Message-ID als Fallback zur BTP-Port-Erkennung

---

## Phase 2: ASN.1-Decoding-Verbesserung (v1.2)

### 2.1 Erweiterte Nachrichtenfelder
- [ ] CAM: Fahrbahnposition (lane position), Fahrzeugabmessungen, Lichter
- [ ] DENM: Ereignistyp (causeCode), Schweregrad, Gültigkeitsdauer
- [ ] MAPEM: Spurbeschreibungen, Geschwindigkeitsbegrenzungen
- [ ] SPATEM: Signalzustände (rot/gelb/grün), Restzeit
- [ ] SREM/SSEM: Signalanforderungsstatus, Priorität
- [ ] Erweiterte `V2xMessage`-Felder oder optionales `decoded_data: dict`

### 2.2 Schema-Management
- [ ] Automatisches Herunterladen neuer ASN.1-Schemata von ETSI
- [ ] Schemaversionen im KML-Export vermerken
- [ ] Validierung der Schema-Integrität (Checksummen)
- [ ] Fallback auf integrierte Schemata bei Download-Fehler

### 2.3 Performance-Optimierung
- [ ] Lazy-Compiling: Schemata nur kompilieren wenn tatsächlich benötigt
- [ ] ASN.1-kompilierte Schemata auf Festplatte cachen (Pickling)
- [ ] Batch-Decoding für große PCAPs (Chunk-Verarbeitung)

---

## Phase 3: Karten- & Visualisierungsverbesserung (v1.3)

### 3.1 Kartenfeatures
- [ ] Offline-Kartenunterstützung (MBTiles oder lokales Tile-Verzeichnis)
- [ ] Kartenlayer-Auswahl (Satellit, Gelände, Verkehr)
- [ ] Heatmap-Overlay für Nachrichtendichte
- [ ] Cluster-Ansicht bei vielen Markern (Leaflet MarkerCluster)
- [ ] Maßstab und Koordinatenanzeige (Mausposition)
- [ ] Screenshot-Export der Kartenansicht

### 3.2 Playback-Verbesserung
- [ ] Zeitleiste mit Miniaturansicht der Nachrichtendichte
- [ ] Loop-Modus (automatisches Wiederholen)
- [ ] Lesezeichen/Sprungmarken in der Zeitleiste
- [ ] Geschwindigkeitsregelung per Slider statt nur ComboBox
- [ ] Frame-für-Frame-Navigation (vor/zurück)

### 3.3 Darstellungsoptionen
- [ ] Verschiedene Marker-Stile (Fahrzeug, Fußgänger, Ampel)
- [ ] Pfeile für Fahrtrichtung (Heading-Visualisierung)
- [ ] Geschwindigkeitsfarbverlauf (langsam=rot, schnell=grün)
- [ ] Höhenprofil als separates Diagramm (matplotlib)
- [ ] Dunkles Karten-Theme (Dark Mode)

---

## Phase 4: Datenanalyse & Export (v1.4)

### 4.1 Statistik-Dashboard
- [ ] Nachrichtenverteilung nach Typ (Balkendiagramm)
- [ ] Zeitlicher Verlauf der Nachrichtenraten
- [ ] Geschwindigkeits-/Heading-Verteilung pro Station
- [ ] Abstandsstatistiken zwischen Stationen
- [ ] CSV-Export der gefilterten Nachrichtendaten

### 4.2 Erweiterter KML-Export
- [ ] Zeitanimierte KML-Dateien (Google Earth Zeitsteuerung)
- [ ] Höhenmodus wählbar (ClampToGround vs. Absolute)
- [ ] Stilvorlagen für verschiedene Nachrichtentypen
- [ ] Netzwerktopologie-Export (Verbindungen zwischen Stationen)
- [ ] Batch-Export: Mehrere PCAPs → mehrere KMLs

### 4.3 Weitere Exportformate
- [ ] GeoJSON-Export
- [ ] GPX-Export (kompatibel mit GPS-Geräten)
- [ ] CSV-Export (flache Tabelle aller Nachrichten)

---

## Phase 5: Architektur & Verteilung (v2.0)

### 5.1 Code-Qualität
- [ ] Type-Checking mit mypy/pyright in CI integrieren
- [ ] Linting mit ruff konfigurieren
- [ ] Formatierung mit black/isort vereinheitlichen
- [ ] Pre-commit-Hooks einrichten
- [ ] GitHub Actions CI-Pipeline

### 5.2 Distribution
- [ ] PyInstaller-Bundle für Windows (.exe)
- [ ] Automatischer Build-Prozess (GitHub Actions)
- [ ] Automatisches Update-Check in der Applikation
- [ ] Portable-Version (USB-Stick-kompatibel)

### 5.3 Performance bei großen Dateien
- [ ] Streaming-Parser für PCAPs > 1 GB (nicht komplett in RAM laden)
- [ ] Lazy-Loading in der Nachrichtentabelle (virtuelles Scrollen)
- [ ] Hintergrund-Thread für PCAP-Parsing (UI bleibt responsiv)
- [ ] Kartenmarker-Optimierung bei > 10.000 Punkten

### 5.4 Erweiterbarkeit
- [ ] Plugin-System für benutzerdefinierte Decoder
- [ ] Konfigurierbare BTP-Port-Zuordnung
- [ ] Unterstützung für benutzerdefinierte ASN.1-Schemata
- [ ] MQTT/UDP-Stream-Empfang für Live-Daten

---

## Priorisierung

| Priorität | Feature | Begründung |
|-----------|---------|-------------|
| **Hoch** | Unit-Tests | Grundlage für alle weiteren Änderungen |
| **Hoch** | Fortschrittsanzeige + Abbrechen | UX für große PCAPs |
| **Hoch** | Erweiterte CAM/DENM-Felder | Kernnutzen der V2X-Analyse |
| **Mittel** | Offline-Karten | Feldanwendung ohne Internet |
| **Mittel** | Zeitanimierter KML-Export | Wichtig für Präsentationen |
| **Mittel** | Statistik-Dashboard | Analyse-Funktionalität |
| **Niedrig** | Plugin-System | Langfristige Erweiterbarkeit |
| **Niedrig** | Live-Stream-Empfang | Out of Scope für v1.x |

---

## ETSI-Standard-Referenzen

| Standard | Beschreibung | Relevant für |
|----------|--------------|-------------|
| EN 302 637-2 V1.4.1 | CAM (Cooperative Awareness Message) | Phase 2.1 |
| EN 302 637-3 V1.3.1 | DENM (Decentralized Environmental Notification) | Phase 2.1 |
| TS 103 301 V2.2.1 | MAPEM/SPATEM/SREM/SSEM | Phase 2.1 |
| TS 102 894-2 V2.2.1 | CDD (Common Data Dictionary) | Phase 2.2 |
| TS 103 248 V2.2.1 | BTP (Basic Transport Protocol) | Phase 1.3 |
| ISO 19091 | DSRC-Nachrichtensatz | Phase 2.2 |