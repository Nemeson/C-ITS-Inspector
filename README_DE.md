# C-ITS Inspector

[![Python Version](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-PyQt6-blue)](https://www.qt.io/)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)](#)
[![Standards](https://img.shields.io/badge/Standards-ETSI%20%7C%20C--Roads-orange)](#)
[![License](https://img.shields.io/badge/License-Proprietary-red)](LICENSE)

[English README](README.md) | **Deutsch**

Die professionelle Desktop-Anwendung zur tiefen Analyse, Validierung und Kartendarstellung von V2X/C-ITS-Nachrichten (ITS-G5 / LTE-V2X) aus PCAP-Dateien und MAP-XML-Geometrien.

---

## 🎯 C-ITS Testservice & Tiefenanalyse

Der **C-ITS Inspector** wurde speziell für technische Entwicklungsteams, Feldtester und Systemintegratoren im C-ITS-Umfeld entwickelt. Er ermöglicht eine detaillierte Dekodierung und Analyse aller relevanten Nachrichtentypen sowie die Überprüfung komplexer Use Cases im Feldbetrieb.

### Unterstützte C-ITS Nachrichtentypen
*   **CAM** (Cooperative Awareness Message) – Fahrzeugzustand, Dynamikdaten, Positionsverläufe.
*   **DENM** (Decentralized Environmental Notification Message) – Ereignisse, Gefahrenmeldungen, Warnzonen.
*   **MAPEM** (Map Data) – Kreuzungstopologien, Fahrspuren (Lanes), Haltelinien, Signalzuordnungen.
*   **SPATEM** (Signal Phase and Timing) – Lichtsignalzustände, Signalprogramme, Zeitprognosen.
*   **SREM / SSEM** (Signal Request / Status Message) – Priorisierungsanfragen von Einsatzkräften/ÖPNV und deren Rückmeldungen von der RSU.
*   **NMEA / GNSS** – Referenz-Positionsdaten zur Überprüfung von GPS-Drift und Positionierungsgenauigkeit.

---

## 🛠 Hauptmerkmale & Use Cases

### 1. C-Roads Konformitätsprüfung (Handbook v3.2.0)
Validieren Sie geladene MAPEM- und SPATEM-Daten direkt im laufenden Betrieb:
*   Prüfung von `IntersectionGeometry` IDs und Revisionen.
*   Geometrische Konsistenzprüfung von Fahrspuren (Ingress/Egress) und Verbindungslinien (Connections).
*   Signalgruppen-Zuordnungsprüfung zwischen Fahrspurgeometrie und aktiven SPATEM-Zuständen.

### 2. Priorisierungs- & Konfliktanalyse (SREM/SSEM)
*   **Request-Korrelation**: Verfolgen Sie Priorisierungsanfragen (SREM) und vergleichen Sie diese direkt mit den Statusrückmeldungen der RSU (SSEM).
*   **Fehler-Panel**: Automatische Erkennung von Timeouts, fehlerhaften Anforderungsprofilen oder Konflikten bei Mehrfachanfragen.
*   **Provenienz**: Rückverfolgbarkeit von Fehlern auf einzelne Capture-Quellen (TXA/RXA) inklusive Konfidenzwerten.

### 3. ETA- & Geschwindigkeitsverifikation
*   Visualisierung des prognostizierten Eintreffens (ETA) an der Haltelinie im zeitlichen Verlauf.
*   Erkennung von Taktabweichungen (Clock-Skew) zwischen Fahrzeugen und Infrastruktur.
*   Ereignistabelle zur schnellen Filterung und Lokalisierung von Unregelmäßigkeiten im Anforderungsprozess.

### 4. Fortgeschrittene Kartendarstellung & Trajektorien-Easing
*   Rendering komplexer Kreuzungstopologien direkt als Vektor-Lageplan (Inbound, Outbound, Stoplines).
*   Umschaltbare Basiskarten (OSM, Satellit, Dunkel, Hell) mit lokalem Caching.
*   **Easing-Algorithmus**: Nicht-lineare Interpolation von Fahrzeugbewegungen zwischen GNSS-Meldungen für eine sprunghafte, realistische Darstellung im Playback.

---

## 🚀 Systemarchitektur & Performance

Die Desktop-App kombiniert PyQt6 mit einer optimierten QtWebEngine/Leaflet-Umgebung für anspruchsvolle Analyseaufgaben:
*   **Lazy Rendering**: Aktualisierung von Kartenlayern und Detail-Inspektoren erfolgt nur für sichtbare Widgets im Vordergrund. Das minimiert IPC-Overhead bei hohen Playback-Geschwindigkeiten (bis zu 10x).
*   **RAM-Watchdog**: Überwachung des App-Speichers zur automatischen Drosselung von Karten-Details (Schonend- oder Diagnose-Modus) bei großen PCAPs.
*   **Lokale Assets**: Leaflet-Bibliotheken sind für den Offline-Betrieb lokal integriert und werden dynamisch geladen.
*   **Streaming-fähiges MessageSource-Protokoll** *(v1.10)*: Das interne `MessageSource`-Protokoll unterstützt jetzt Streaming-Semantik — `state`, `stats`, `pause()`, `resume()`, `on_event()`. Ein gemeinsamer `DefaultMessageSourceMixin` reduziert Boilerplate. `PcapFileSource` nutzt Lazy-Iteration (kein Eager-Parse bei `duration()`-Abfrage mehr).

---

## 📋 Letzte Aktualisierungen (v1.10 — Pre-Live-Vorbereitung)

Diese Version konzentriert sich auf **architektonische Härtung** für die kommende Live-Capture-Phase (v2.0). Keine neuen Endbenutzer-Features, primär ein Meilenstein für Code-Qualität und UI-Konsistenz.

### Architektur
- **Streaming-fähiges `MessageSource`-Protokoll**: Additive Member (`state`, `stats`, `pause`, `resume`, `on_event`) mit `SourceState`-Enum und `SourceStats`-Dataclass. Alle bestehenden Quellen (`PcapFileSource`, `XmlMapSource`, `SessionMessageSource`, `CombinedMessageSource`) sind abwärtskompatibel.
- **`PcapFileSource` Lazy Streaming**: `iter_messages()` ist ein Single-Use-Generator; `duration()` ist gecacht (kein Eager-Parse-Bug mehr).
- **Live-Quellen-Skeletons**: `Esp32MqttSource` (OpenTrafficMap-Firmware-Integration — Phase 4 wird die echte MQTT-Subscription einbauen), `CohdaMk6Source` + `OpenC2XSource` (Skeleton-Stubs, die das Protokoll erfüllen).

### UI
- **Top-Toolbar bereinigt**: 5 Export-Buttons (KML, Fehler, Diagnose, Dashboard, Bericht) sind in dedizierte Menüs verschoben.
- **Neue Menü-Reihenfolge**: Datei → **Export** → Optionen → **Ansicht** → Hilfe. Das „Export"-Menü gruppiert die vier Export-Funktionen; „Ansicht" enthält das Dashboard.
- **Workspace-Toolbar visuell an Haupttoolbar angepasst** (Default-Qt-Grau, Padding für Tab-Buttons behoben — Buchstaben wie „M" in „MAP-Analyse" werden nicht mehr abgeschnitten).
- **Profile-Switcher verbreitert** (160 → 240 px), damit alle drei Profile (Analyst, Feldtester, Einsteiger) ohne Scrollen sichtbar sind.

### Qualität
- **745 Tests grün, 0 Failures** (von 689 in v1.9).
- Bugfix: `PcapFileSource.duration()` triggert nicht mehr den vollen PCAP-Parse.
- Bugfix: Mixin-State hat zwischen Instanzen geleakt (Klassen-Attribute) — behoben durch per-Instance-Init.
- Bugfix: Inline-`QToolButton`-Stylesheet wurde von Qt-Internals überschrieben — ersetzt durch `QPushButton#wsGroupTab`-objectName-Stylesheet.

### Roadmap
- v1.8 (1.8.0): ✅ Abgeschlossen
- v1.9: ✅ Abgeschlossen (SPAT-Analyse)
- **v1.10**: ✅ **Abgeschlossen** (Pre-Live-Vorbereitung — diese Version)
- v2.0: 🚧 In Entwicklung (echte MQTT-Integration mit OpenTrafficMap-Firmware)

---

## 💻 Erste Schritte

### Voraussetzungen
*   Windows 10 oder Windows 11
*   Python >= 3.11 und Abhängigkeiten (siehe `pyproject.toml`)
*   *Optional*: Wireshark / TShark für eine erweiterte PCAP-Dekodierung (beschleunigt das Parsing signifikant).

### Installation & Start
Der freie Download der Demo-Version ist unter folgendem Link verfügbar: [C-ITS-Inspector.exe](https://drive.google.com/file/d/1p54nI-e_UJO4Gr8u9W-sWpO_6mTC0klo/view?usp=sharing)

1.  Klonen Sie das Repository oder entpacken Sie das Release-Paket.
2.  Installieren Sie die Abhängigkeiten:
    ```powershell
    pip install .[dev]
    ```
3.  Starten Sie den Player über den komfortablen Launcher:
    ```powershell
    python c_its_inspector_launcher.py
    ```

---

## 🔒 Lizenz und Vertrieb

Dieses Produkt ist **proprietär** und urheberrechtlich geschützt.

> [!IMPORTANT]
> **Nutzungsrechte im Überblick:**
> *   **Urheberrecht**: Copyright (c) 2026 Kevin Seipel. Alle Rechte vorbehalten.
> *   **Kevin Seipel**: Uneingeschränkte Nutzung gestattet.
> *   **Dritte (nicht-kommerziell / akademisch)**: Nutzung gestattet, solange diese Erlaubnis nicht vom Urheber widerrufen wird (Widerruf ist jederzeit und ohne Angabe von Gründen möglich).
> *   **Forschungsinstitute**: Erhalten auf Anfrage beim Vertrieb eine kostenlose Lizenz für 0,5 Jahre (6 Monate). Verlängerungen dieser Lizenz sind ganz klar NICHT ausgeschlossen.
> *   **Kommerzielle Nutzung**: Strikte Lizenzpflicht. Kommerzielle Nutzung ohne eine gültige Lizenz ist untersagt. Lizenzen sind für 1 Jahr ab Erwerb gültig.

### Lizenzerwerb
Für Anfragen zu kommerziellen Lizenzen, Preisen oder individuellen Angeboten wenden Sie sich bitte direkt an den Vertrieb:

📧 **E-Mail**: **[vertrieb@seipel.uk](mailto:vertrieb@seipel.uk)**
