# Changelog

Dieses Changelog dokumentiert den aktuell rekonstruierten Entwicklungsstand der App auf Basis des vorhandenen Repos.

Das Format orientiert sich an Keep a Changelog.  
Eine lueckenlose Historie vor dem dokumentierten Stand wurde nicht rueckwirkend aus Commits rekonstruiert.

## [1.3.0] - 2026-04-18

### Added

- Persistentes App-Memory fuer letzte Sitzung, letzte Verzeichnisse und Sitzungszusammenfassungen
- Drag & Drop fuer `.pcap`, `.pcapng` und `.cap`
- Hintergrund-Parsing mit Fortschrittsanzeige und Abbrechen-Funktion
- globale Exception-Behandlung beim App-Start
- PKI-/Security-Detailanzeige fuer ETSI-TS-103-097-bezogene Felder
- Szenen-Aggregation mit `IntersectionState`, `SignalGroupState`, `SpatForecast`, `ActiveRequest` und `SceneSnapshot`
- Szenenpanel in der UI mit
- Kreuzungsstatus
- offenen Anforderungen
- Inline-Warnungen
- 30s-Phasen-Timelines
- Statistikfeldern fuer Nachrichtenrate und ETA-Abweichung
- Clock-Skew-Erkennung zwischen SPAT-Zeit und PCAP-Zeitstempel
- ETA-Verifikation ueber CAM-Trajektorien und MAP-Referenzpunkte
- ASN.1-Schema-Update aus Git
- Integritaetspruefung fuer Schemadateien
- Schema-Provenance im KML-Export
- Festplatten-Cache fuer kompilierte ASN.1-Schemata
- Reale Test-PCAP-Dateien und umfassendere `pytest`-Suite

### Changed

- Parser-Robustheit fuer `pyshark` und `scapy` deutlich erweitert
- ITS-Nachrichtenerkennung verbessert durch BTP-Port-Logik und `messageId`-Fallback aus dem ITS-PDU-Header
- GeoNetworking-/BTP-Erkennung fuer direkten ITS-G5-Traffic erweitert
- UI visuell in Richtung SWARCO-ITS-inspirierter Operator-Oberflaeche ueberarbeitet
- KML-Export auf Windows-sichere Dateinamen und Kollisionsvermeidung gehaertet
- MAPEM-, SPATEM-, SREM- und SSEM-Zusatzfelder in `decoded_data` deutlich vertieft

### Fixed

- KML-Export scheiterte bei Station-IDs mit unter Windows ungueltigen Zeichen wie `:`
- KML-Dateinamenskollisionen nach Sanitizing werden nun aufgeloest
- Parser-Fallback bei fehlendem BTP-Port ueber ITS-PDU-Header
- stabilerer Lade-Workflow bei grossen oder fehlerhaften Captures

### Testing

- Teststand zum dokumentierten Zeitpunkt: `102 passed`

## [Unreleased]

### Planned

- Flow-Freigabe-Check ueber MAP-Lane-Verknuepfungen
- weitere Karten- und Visualisierungsfunktionen aus Phase 3
- CSV-, GeoJSON- und GPX-Export
- tiefere PKI-Ketten- und Signaturvalidierung
