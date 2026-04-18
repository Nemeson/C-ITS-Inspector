# PCAP2KML Player

Desktop-Anwendung zur Analyse und Visualisierung von V2X-Nachrichten aus PCAP-Dateien.  
Die App kombiniert PCAP-Parsing, ASN.1-Decoding, interaktive Kartenansicht, synchronisierte Wiedergabe, KML-Export und ein Szenen-Panel fuer MAP/SPAT/SREM/SSEM.

Stand: 2026-04-18  
Aktueller dokumentierter Funktionsstand: v1.3

## Uebersicht

PCAP2KML Player ist auf ITS-G5 / ETSI-V2X-Workflows ausgelegt. Die Anwendung liest `.pcap`, `.pcapng` und `.cap`, dekodiert erkannte ITS-Nachrichten sowie NMEA-Daten und stellt sie in einer operativen Desktop-Oberflaeche dar.

Aktuell unterstuetzt die App insbesondere:

- CAM
- DENM
- MAPEM
- SPATEM
- SREM
- SSEM
- NMEA / GNSS

## Kernfunktionen

- Multi-Datei-PCAP-Import mit Hintergrund-Parsing, Fortschrittsanzeige und Abbrechen-Funktion
- Drag & Drop fuer Capture-Dateien
- Persistente "Letzte Sitzung"-Funktion inklusive letzter Verzeichnisse und Sitzungszusammenfassung
- Interaktive Leaflet-Karte im Desktop-Fenster mit Marker- und Trajektoriendarstellung
- Synchronisierte Wiedergabe mit `Play`, `Pause`, `Stop`, Scrubbing und Geschwindigkeiten von `0.1x` bis `10x`
- Live-Filter nach Nachrichtentyp und Station-ID
- Detailansicht pro Nachricht inklusive PKI-/Security-Felder
- KML-Export pro Station, kompatibel mit Google Earth und QGIS
- ASN.1-Schema-Update aus Git plus Schema-Provenance im Export
- Szenen-Aggregation fuer MAP/SPAT/SREM/SSEM
- MAP-zu-SPAT-Join ueber `intersectionId`
- Phasenprognose fuer die naechsten 30 Sekunden
- Korrelation offener Anforderungen aus SREM/SSEM
- Timeout-Erkennung fuer unbeantwortete Anforderungen
- Clock-Skew-Erkennung zwischen DSRC-Zeit und PCAP-Zeitstempel
- ETA-Verifikation ueber CAM-Trajektorien relativ zur MAP-Referenzposition

## UI im aktuellen Stand

Die Hauptansicht besteht aus vier Arbeitsbereichen:

1. Kopfbereich mit Sitzungsstatus, Dateianzahl, Nachrichtenzahl und Stationen
2. Filterzeile fuer Nachrichtentypen und Stationen
3. Karten- und Tabellensicht mit Nachrichtentabelle, Detailtabelle und Szenenpanel
4. Playback-Leiste mit Slider, Zeitanzeige und Geschwindigkeitsumschaltung

Das Szenenpanel zeigt derzeit:

- Kreuzungen mit MAP-/SPAT-Revisionen
- Signalgruppen-Zusammenfassung
- kompakte 30s-Phasen-Timelines
- offene Anforderungen mit Prioritaet und Lane-Bezug
- Inline-Warnungen bei fehlender MAP-Basis, Revisionsmismatch, Timeout und Clock Skew
- Kennzahlen wie `Msgs/s` und mittlere ETA-Abweichung

## Architektur

### Parser und Decoding

- `pcap_parser.py` nutzt `pyshark` bevorzugt, faellt aber auf `scapy` zurueck
- Direkte GeoNetworking-/BTP-Erkennung fuer EtherType `0x8947`
- Fallback-Nachrichtenerkennung ueber ITS-PDU-Header `messageId`
- NMEA-Parsing fuer GNSS-Daten
- ASN.1-Decoding ueber `asn1tools`

### Playback und Visualisierung

- `player_controller.py` steuert die synchronisierte Wiedergabe
- `map_widget.py` bettet Leaflet in `QWebEngineView` ein
- `ui/main_window.py` verbindet Playback, Filter, Export und Szenenpanel

### Szenenmodell

`scene_model.py` aggregiert den flachen Nachrichtenstrom zu fachlichen Zustandsobjekten:

- `IntersectionState`
- `SignalGroupState`
- `SpatForecast`
- `ActiveRequest`
- `SceneSnapshot`
- `EtaVerification`

### Security / PKI

`security_parser.py` extrahiert bereits Grundinformationen aus ETSI TS 103 097 Security-Containern, darunter Signer-Typ, Signaturdaten, Gueltigkeit und weitere Zertifikatsfelder. Die tiefe Signatur- und Kettenpruefung ist noch nicht vollstaendig umgesetzt.

## Projektstruktur

```text
PCAP2KML/
├── docs/
│   └── ROADMAP.md
├── pcap2kml_player/
│   ├── app_memory.py
│   ├── asn1_schemas.py
│   ├── data_model.py
│   ├── kml_exporter.py
│   ├── main.py
│   ├── map_widget.py
│   ├── nmea_parser.py
│   ├── parsing_worker.py
│   ├── pcap_parser.py
│   ├── player_controller.py
│   ├── scene_model.py
│   ├── security_parser.py
│   ├── ui/
│   │   └── main_window.py
│   ├── assets/
│   │   └── cache/
│   └── requirements.txt
├── testfiles/
├── tests/
├── CHANGELOG.md
└── README.md
```

## Voraussetzungen

- Windows 10 oder 11
- Python 3.11+
- Wireshark / TShark optional, aber empfohlen fuer `pyshark`

Hinweis: Ohne `TShark` funktioniert die App weiterhin ueber den `scapy`-Fallback, allerdings mit moeglicherweise eingeschraenkter Decoderabdeckung je Capture.

## Installation

```powershell
cd C:\PythonTools\PCAP2KML\pcap2kml_player
py -m pip install -r requirements.txt
```

## Anwendung starten

```powershell
cd C:\PythonTools\PCAP2KML
py pcap2kml_player\main.py
```

## Abhaengigkeiten

| Paket | Zweck |
|---|---|
| `PyQt6` | Desktop-GUI |
| `PyQt6-WebEngine` | eingebettete Karte |
| `scapy` | Fallback-PCAP-Backend |
| `pyshark` | bevorzugtes PCAP-Backend ueber TShark |
| `asn1tools` | ASN.1-Decoding |
| `simplekml` | KML-Erzeugung |

## Bedienung

### Laden

- `PCAP laden` oeffnet einen Dateidialog
- `.pcap`, `.pcapng` und `.cap` koennen auch direkt ins Fenster gezogen werden
- `Letzte Sitzung` laedt die zuletzt erfolgreich geoeffneten Dateien erneut
- `Laden abbrechen` stoppt einen laufenden Parse-Vorgang

### Filtern und Abspielen

- Nachrichtentypen lassen sich per Checkbox ein- und ausblenden
- Stationen lassen sich in der Stationsliste selektieren
- Der Slider springt an beliebige Zeitpunkte
- Die Marker-Hervorhebung folgt der Wiedergabe

### Export

- `KML exportieren` schreibt eine KML-Datei pro Station
- Dateinamen werden fuer Windows sicher bereinigt
- Kollisionen nach Sanitizing werden automatisch aufgeloest
- Exportierte Dokumente enthalten die verwendeten ASN.1-Schemaversionen

## Test- und Qualitaetsstand

Die aktuelle Testsuite umfasst den Kern der Parser-, Export- und Szenenlogik.

- Aktueller Stand: `102 passed`
- Vorhandene Testbereiche
- Datenmodell
- NMEA-Parser
- PCAP-Parser
- Parser-Zusatzfelder
- KML-Export
- Player-Controller
- App-Memory
- Security-Parser
- Szenenmodell

Noch offen sind vor allem direkte Tests fuer:

- `ui/main_window.py`
- `map_widget.py`
- `parsing_worker.py`
- den eigentlichen Application-Entry-Point

## Bekannte Grenzen

- Kein vollstaendiger PKI-Chain-Validator
- Noch kein CSV-, GeoJSON- oder GPX-Export
- Noch keine Offline-Karten oder Layer-Umschaltung
- Keine dedizierte dichte Timeline / keine Frame-fuer-Frame-Navigation
- Keine Headless-CLI

## Roadmap

Der detaillierte Umsetzungsstand liegt in [docs/ROADMAP.md](C:/PythonTools/PCAP2KML/docs/ROADMAP.md).

Naechste groessere Themen:

- weitere Karten- und Visualisierungsfunktionen aus Phase 3
- Exportformate aus Phase 4
- Architektur- und Distributionsarbeit aus Phase 5

## Changelog

Das projektspezifische Aenderungsprotokoll liegt in [CHANGELOG.md](C:/PythonTools/PCAP2KML/CHANGELOG.md).
