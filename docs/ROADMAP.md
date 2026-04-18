# PCAP2KML Player — Roadmap

**Stand:** 2026-04-18 | **Version:** 1.1

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

## Phase 2.5: PKI-Signatur-Analyse (v1.25)

### 2.5.1 ETSI TS 103 097 Security Header — Extrahierbare Daten

ETSI ITS G5 Nachrichten können mit einem Security Envelope (IEEE 1609.2 / ETSI TS 103 097) signiert sein. Die folgende Tabelle zeigt alle Felder, die aus dem Security Header extrahiert werden können:

| Feld | ASN.1-Typ | Beschreibung | ETSI-Referenz |
|------|-----------|--------------|---------------|
| **Protocol Version** | `Uint8` | Sicherheitsprotokoll-Version (2 = aktuell) | TS 103 097 §5.1 |
| **Security Profile** | ENUM | `unsecured`, `signed`, `signed_encrypted`, `signed_encrypted_auth` | TS 103 097 §5.2 |
| **Signer Type** | CHOICE | `self` (Selbstsigniert), `digest` (Zertifikat-Hash), `certificate_chain` (Zertifikatskette) | TS 103 097 §6.3 |
| **Signer Digest** | `HashedId8` | SHA-256 Hash der Signaturzertifikats (ersten 8 Bytes) | TS 103 097 §6.3 |
| **Certificate Issuer** | `HashedId8` | SHA-256 Hash der ausstellenden CA | TS 103 097 §7.1 |
| **Certificate Subject Type** | ENUM | `CA`, `subscriber`, `enrollment_CA` | TS 103 097 §7.2 |
| **Validity Start** | `Time64` | Zertifikatsgültigkeit: Startzeitpunkt (Unix epoch µs) | TS 103 097 §7.4 |
| **Validity End** | `Time64` | Zertifikatsgültigkeit: Endzeitpunkt (Unix epoch µs) | TS 103 097 §7.4 |
| **Signature Algorithm** | CHOICE | `ECDSA NIST P-256` oder `ECDSA BrainpoolP256r1` | TS 103 097 §5.4 |
| **Signature R** | `EcdsaP256Signature` | R-Wert der ECDSA-Signatur (32 Bytes, gekürzt dargestellt) | TS 103 097 §5.4 |
| **Signature S** | `EcdsaP256Signature` | S-Wert der ECDSA-Signatur (32 Bytes, gekürzt dargestellt) | TS 103 097 §5.4 |
| **Assurance Level** | `SubjectAssurance` | Vertrauensstufe 0-7 (TS 102 941) | TS 102 941 §6.2 |
| **Station Type** | `StationType` | Fahrzeugtyp: `passengerCar`, `bus`, `roadSideUnit`, etc. | TS 102 894-2 §7.1 |
| **ITS-AID List** | `SequenceOfPsid` | Autorisierte ITS-Application-Identifier (z.B. 36=CAM/DENM, 121=IS) | TS 102 965 |
| **SSP Permissions** | `ServiceSpecificPermissions` | Dienstspezifische Berechtigungen (hex oder lesbar) | TS 103 097 §7.5 |
| **Region Type** | ENUM | `none`, `circular`, `rectangular`, `polygonal`, `country` | TS 103 097 §7.6 |
| **Region Detail** | UNION | Ländercode (z.B. DE), Koordinaten oder Polygon je nach Regionstyp | TS 103 097 §7.6 |

### 2.5.2 Implementierungsstatus

- [x] `SecurityInfo`-Datenklasse in `data_model.py`
- [x] `security_parser.py` — Parsen des Security Envelopes (ETSI TS 103 097 V2.2.1)
- [x] Extraktion aus Rohebenen (Protokollversion, Profil, Signer-Info, Signatur)
- [x] Extraktion aus dekodierten ASN.1-Nachrichten (Station-Typ, ITS-AIDs)
- [x] Detail-Tabelle in der UI (Klick auf Nachricht zeigt PKI-Details)
- [ ] Zertifikatsketten vollständig parsen (DER/UPER dekodierung)
- [ ] Zertifikatsgültigkeitsprüfung (Ablaufdatum vs. aktueller Zeit)
- [ ] Signaturverifikation (ECDSA-Validierung gegen öffentlichen Schlüssel)
- [ ] Vertrauenskette-Validierung (Wurzelzertifikat → CA → Subscriber)
- [ ] CRL-Prüfung (Certificate Revocation Lists)
- [ ] Anzeige der Zertifikatskette als Baumstruktur

### 2.5.3 ETSI PKI-Referenzen

| Standard | Beschreibung | Relevanz |
|----------|--------------|---------|
| ETSI TS 103 097 V2.2.1 | Security header und Zertifikatsformate | Hauptreferenz für Signatursanalyse |
| ETSI TS 102 941 V1.4.1 | ITS Trust Management (PKI-Vertrauensmodell) | CA-Hierarchie, Zertifikatsvergabe |
| ETSI TS 102 965 | ITS Application Identifiers (ITS-AIDs) | Zuordnung ITS-AID → Nachrichtentyp |
| IEEE 1609.2 | Security Services for V2X | Grundlage für Security Envelope |
| ETSI TS 102 894-2 | Common Data Dictionary (CDD) | StationType und andere Aufzählungen |
| ETSI TS 103 301 | IS Message Types (MAPEM/SPATEM/SREM/SSEM) | SSP-Berechtigungen für IS-Nachrichten |

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