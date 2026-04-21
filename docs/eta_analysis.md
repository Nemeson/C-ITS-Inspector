# ETA-Analyse

Stand: 2026-04-21

Die ETA-Analyse ist request-zentriert. Sie ist nicht mehr nur eine einfache
Zeitreihe pro Station, sondern eine Diagnoseansicht fuer eine konkrete
Priorisierungsanforderung.

## Auswahl

Die Auswahl erfolgt ueber:

```text
Intersection-ID
Request-ID
Sequence Number
Station-ID
Merge-Gruppe, falls vorhanden
```

Label-Beispiel:

```text
I72 R6/S86 | 2228620000 | Merge merge-12
```

## Zeitachse

Die Zeitachse startet relativ zur ersten passenden SREM:

```text
t = 0.0 s -> erste SREM der gewaehlten Request-Spur
```

Das macht Requests vergleichbar, auch wenn mehrere PCAPs oder Kreuzungen geladen
werden.

## Dargestellte Reihen

- Blaue Kurve: Restzeit bis Stopline
- Gruene Kurve: geglaettete Geschwindigkeit
- Vertikale blaue Linien: SREM-Updates
- Farbiges Band: SSEM-Status
- Diagnosemarker: ETA-Spruenge, fehlendes SSEM, spaetes Granted, ETA-Konflikte

## Geschwindigkeit

Die Geschwindigkeit wird als kleiner gleitender Mittelwert dargestellt. Das ist
absichtlich geglaettet, weil einzelne PCAP-/GNSS-Jitter sonst den fachlichen
Trend ueberdecken.

## Stopline-Verifikation

Die ETA-Verifikation nutzt bevorzugt:

```text
MAP Stopline der inLane
```

Fallback:

```text
MAP RefPoint
```

Eine ETA gilt aktuell als genau, wenn die Abweichung hoechstens 2 Sekunden
betraegt.

## SREM/SSEM-Darstellung

SREM:

```text
vertikale Eventlinie mit Request-ID, Sequence und ETA-Restzeit
```

SSEM:

```text
Statusband, z. B. processing -> granted
```

Dadurch ist sichtbar, ob die Antwort der Infrastruktur rechtzeitig vor der
Stopline-Passage kam.

## Diagnosehinweise

Die ETA-Ansicht nutzt dieselben fachlichen Annahmen wie die Priorisierungsanalyse.
Sie hebt unter anderem hervor:

- ETA springt stark
- ETA steigt trotz Annaeherung
- SREM ohne SSEM
- kein `granted`
- spaetes `granted`
- Stopline-Passage ohne `granted`
- ETA-Abweichung groesser Toleranz
