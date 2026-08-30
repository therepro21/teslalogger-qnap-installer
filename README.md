# TeslaLogger QNAP Manager

Eine vollständig klickbare Installation und Verwaltung von [TeslaLogger](https://github.com/bassmaster187/TeslaLogger) für QNAP Container Station 3 – ohne SSH, ohne Bash und ohne manuell gepflegte Compose-Dateien.

[![Validate, test and publish](https://github.com/therepro21/teslalogger-qnap-installer/actions/workflows/ci.yml/badge.svg)](https://github.com/therepro21/teslalogger-qnap-installer/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> Inoffizielles Community-Projekt; nicht verbunden mit oder unterstützt von Tesla, TeslaLogger, QNAP Systems, Docker, MariaDB oder Grafana Labs.

## QNAP-App-Template-URL

Diese öffentliche URL wird direkt in Container Station 3 eingetragen:

```text
https://raw.githubusercontent.com/therepro21/teslalogger-qnap-installer/main/qnap-template.json
```

## Installation – Klick für Klick

1. Im QNAP App Center **Container Station 3** installieren und öffnen.
2. In Container Station **Einstellungen / Preferences** öffnen.
3. **App Templates** auswählen.
4. **Benutzerdefiniertes Template aktivieren** einschalten.
5. Die oben angegebene Raw-GitHub-URL einfügen.
6. **Anwenden** anklicken.
7. Zu **App Templates > Custom Templates** wechseln.
8. Das zur QNAP-CPU passende Template wählen:
   - **TeslaLogger QNAP Manager (Intel/AMD64)** für `x86_64`
   - **TeslaLogger QNAP Manager (ARM64)** für `aarch64`
9. **Deploy / Bereitstellen** anklicken.
10. Warten, bis der Manager-Container als „Running“ angezeigt wird.
11. In Container Station beim Manager den automatisch zugewiesenen Host-Port für Container-Port `8080` ablesen.
12. Das Container-Log öffnen und das einmalig erzeugte Manager-Passwort kopieren.
13. Im Browser `http://QNAP-IP:ZUGEWIESENER-PORT` öffnen.
14. Mit Benutzer `admin` und dem Passwort aus dem Container-Log anmelden.
15. Interne IP, Ports, Zeitzone und optional Domain/HTTPS eintragen.
16. **Ports prüfen & anwenden** anklicken.

Die erste TeslaLogger-Initialisierung kann auf langsameren NAS-Systemen 10 bis 30 Minuten dauern. Status und Fehlermeldungen erscheinen im Manager.

## Manager-Adresse und Sicherheit

Der Manager lauscht intern auf Port `8080`. Das QNAP-Template gibt keinen festen Host-Port vor; Docker wählt automatisch einen freien Port. Dadurch kann die Manager-Installation nicht an einem bereits belegten Host-Port scheitern.

```text
http://QNAP-IP:AUTOMATISCH_ZUGEWIESENER_PORT
```

- Benutzer: `admin`
- Passwort: beim ersten Start kryptografisch zufällig erzeugt
- Speicherung: ausschließlich im Volume `teslalogger_qnap_manager_data`, Modus `0600`
- Zugriff: nur private, lokale und Link-Local-Clientadressen werden akzeptiert

**Den Manager-Port niemals am Router ins Internet weiterleiten.** Für administrativen Fernzugriff ausschließlich VPN oder einen korrekt abgesicherten HTTPS-Reverse-Proxy mit zusätzlicher Authentifizierung verwenden.

## Grafische Konfiguration

Im Browser können später jederzeit geändert werden:

| Einstellung | Standard | Bedeutung |
| --- | --- | --- |
| Interne Bind-IP | `0.0.0.0` | QNAP-IP beziehungsweise lokale Schnittstelle für veröffentlichte App-Ports |
| TeslaLogger-Port | `5010` | TeslaLogger-API, Container-intern `5000` |
| Grafana-Port | `3000` | Grafana, Container-intern `3000` |
| Admin-Port | `8888` | TeslaLogger-Adminoberfläche, Container-intern `80` |
| Zeitzone | `Europe/Berlin` | Zeitzone aller Anwendungscontainer |
| Domain / externe IP | leer | Später änderbare öffentliche Adresse für Anzeige und Reverse Proxy |
| Schema | `http` | `http` oder `https` für die externe Adresse |

Die Domain ist keine automatische DNS- oder Zertifikatseinrichtung. Der Manager zeigt das passende Reverse-Proxy-Ziel an; DNS, QNAP Reverse Proxy und TLS-Zertifikate werden weiterhin in QTS beziehungsweise beim verwendeten Proxy verwaltet.

## Portprüfung und bestehende Container

Vor der Installation beziehungsweise jeder Portänderung führt der Manager zwei Prüfungen aus:

1. Er sucht alle laufenden Docker-Container, die den gewünschten Host-Port veröffentlichen.
2. Er startet kurzzeitig einen minimalen Bind-Testcontainer, um auch Konflikte mit QTS, QuFirewall oder Nicht-Docker-Diensten zu erkennen.

Ist ein Port belegt, wird innerhalb der nächsten 100 Portnummern der erste freie Port gewählt und die Anpassung angezeigt. Beispiel: Läuft bereits ein anderes Grafana auf `3000`, werden `3001`, `3002` usw. geprüft.

Eine andere MariaDB auf dem QNAP ist unproblematisch: Die TeslaLogger-MariaDB bleibt ausschließlich im eigenen Compose-Netz und veröffentlicht **keinen** Host-Port `3306`.

Existieren bereits Container mit den Namen `teslalogger`, `teslalogger-db`, `teslalogger-grafana` oder `teslalogger-webserver`, die nicht von diesem Manager erzeugt wurden, bricht die Einrichtung ab. Vorhandene Container oder Daten werden nicht verändert.

## Kontrollierte Updates

Updates werden bewusst im Manager gestartet. Watchtower ist in dieser verwalteten Variante nicht enthalten, da unbeaufsichtigte Updates die geforderte Backup- und Prüfsequenz umgehen würden.

Bei **Backup & Update** geschieht in dieser Reihenfolge:

1. Konsistenter SQL-Dump der MariaDB
2. Kurzes Pausieren der schreibenden Anwendungscontainer
3. Archivierung aller Datei-, Konfigurations-, Dashboard- und Rechnungsvolumes
4. Speicherung von Konfiguration, Secrets und Backup-Manifest
5. Markierung der bisherigen Images als lokale Rollback-Images
6. Laden neuer TeslaLogger-, Grafana- und Webserver-Images
7. Ausschließliches Ersetzen der Container; Volumes werden wiederverwendet
8. Prüfung von Containerstatus und Healthchecks
9. Bei Fehlern verständliche Meldung und erneute Aktivierung der vorherigen Images

MariaDB bleibt auf `10.4.7` fixiert und wird bei einem normalen Update nicht angehoben. Der Manager verwendet den Major-Tag `:1`. Ein späteres Major-Upgrade erfordert eine bewusst geänderte Template-/Imageversion und eigene Migrationshinweise.

TeslaLogger veröffentlicht seine drei projektspezifischen Images derzeit nur über bewegliche `latest`-Tags. Der Manager kontrolliert deshalb den Zeitpunkt des Pulls, erstellt vorher zwingend ein Backup und hält lokale Rollback-Tags vor. Ein Container-Recreate ohne Update verwendet vorhandene lokale Images.

## Backup und Restore

Ein Backup enthält:

- vollständigen SQL-Dump der MariaDB, wenn die Datenbank läuft
- alternativ ein Offline-Archiv des MariaDB-Volumes
- TeslaLogger-Daten und interne Backups
- Rechnungen
- Grafana-Datenbank, Dashboards und Plugins
- SQL-Schema- und temporäre Anwendungsdaten
- Manager-Konfiguration und zufällig generierte Secrets
- Compose-Datei und maschinenlesbares Manifest

Backups liegen im persistenten Volume `teslalogger_qnap_backups` und können direkt über die Manager-Oberfläche heruntergeladen werden.

Restore erfordert die zusätzliche Eingabe `RESTORE`. Vor jedem Restore erzeugt der Manager automatisch ein weiteres Sicherheitsbackup, stoppt nur die verwalteten Container, stellt Volumes und Datenbank wieder her und führt anschließend Healthchecks aus.

Backup-Archive enthalten Secrets und möglicherweise personenbezogene Fahrzeug- und Standortdaten. Sie müssen entsprechend geschützt und verschlüsselt aufbewahrt werden.

## Persistente Volumes – niemals löschen

| Volume | Inhalt |
| --- | --- |
| `teslalogger_qnap_manager_data` | Manager-Passwort, Konfiguration, Secrets und Compose-Zustand |
| `teslalogger_qnap_backups` | herunterladbare Backup-Archive |
| `teslalogger_qnap_mysql` | MariaDB-Datenbank |
| `teslalogger_qnap_data` | TeslaLogger-Anwendungsdaten |
| `teslalogger_qnap_app_backup` | interne TeslaLogger-Backups |
| `teslalogger_qnap_invoices` | Tesla-Rechnungen |
| `teslalogger_qnap_grafana` | Grafana-Datenbank und Einstellungen |
| `teslalogger_qnap_grafana_dashboards` | Grafana-Dashboards |
| `teslalogger_qnap_grafana_plugins` | Grafana-Plugins |
| `teslalogger_qnap_sqlschema` | TeslaLogger-SQL-Schema |
| `teslalogger_qnap_tmp` | zwischen TeslaLogger und Webserver geteilte Daten |

Die Anwendungsvolumes sind in Compose als `external: true` markiert und tragen zusätzlich das Label `io.teslalogger.qnap.protected=true`. `docker compose down` kann sie dadurch nicht versehentlich löschen. Container dürfen beliebig ersetzt werden; die Volumes bleiben erhalten.

## Domain oder Reverse Proxy später ändern

1. Manager im Browser öffnen.
2. Unter **Einrichtung & Netzwerk** Domain/IP und `http` oder `https` ändern.
3. **Ports prüfen & anwenden** anklicken.
4. Das angezeigte interne Reverse-Proxy-Ziel in QTS übernehmen.
5. DNS und Zertifikat außerhalb des Managers prüfen.

Der Manager ändert keine DNS-Zonen, Routerfreigaben oder Zertifikate automatisch.

## Deinstallation

### Anwendung entfernen, Daten behalten

Im Manager **Nur Container entfernen, Daten behalten** anklicken. Die Container und das Compose-Netz werden entfernt; alle oben genannten Volumes bleiben bestehen. Eine spätere erneute Bereitstellung kann dieselben Daten verwenden.

### Vollständige Deinstallation einschließlich Daten

1. Im Manager die Warnhinweise lesen.
2. Exakt `ALLE DATEN LOESCHEN` eingeben.
3. **Container und Datenvolumes entfernen** anklicken.
4. Der Manager erstellt zuerst ein letztes Backup.
5. Erst danach entfernt er die Anwendungscontainer und Anwendungsvolumes.
6. Abschließend den Manager-Container in Container Station löschen.
7. Nur wenn auch Manager-Zugang und Backups endgültig entfernt werden sollen, in Container Station zusätzlich `teslalogger_qnap_manager_data` und `teslalogger_qnap_backups` löschen.

Die beiden vom laufenden Manager selbst verwendeten Volumes werden absichtlich nicht aus dem Manager heraus gelöscht. Dadurch kann eine Fehlbedienung nicht gleichzeitig die letzte Sicherung vernichten.

## Architektur und Images

Unterstützt:

- `linux/amd64`: 64-Bit Intel/AMD-QNAP
- `linux/arm64`: 64-Bit ARM-QNAP

Nicht unterstützt:

- `linux/arm/v7`, `armhf` und andere 32-Bit-ARM-Systeme
- QNAP-Modelle ohne Container Station 3 beziehungsweise Docker Compose v2
- andere CPU-Architekturen wie MIPS

Der Manager verweigert den Start auf nicht unterstützten Architekturen mit einer klaren Fehlermeldung. Die verwendeten TeslaLogger-, Grafana-, Webserver-, MariaDB-, Alpine- und Manager-Images wurden auf vorhandene AMD64- und ARM64-Manifeste geprüft.

## Docker-Socket

Der Manager benötigt `/var/run/docker.sock`, um Volumes anzulegen, Ports zu testen, Compose-Container zu ersetzen und Backups aus Volumes zu erstellen. Zugriff auf diesen Socket entspricht praktisch administrativen Rechten über Docker und damit weitreichenden Rechten auf dem NAS.

Die Nutzung wird begrenzt:

- nur der Manager erhält den Socket
- der Manager läuft nicht im privilegierten Modus
- TeslaLogger, MariaDB, Grafana und Webserver erhalten den Socket nicht
- die Weboberfläche akzeptiert nur lokale/private Client-IP-Adressen
- zufälliges Passwort, CSRF-Token und restriktive Browser-Header
- keine Telemetrie und keine Speicherung von GitHub- oder Tesla-Tokens im Image

## Entwicklung und Qualitätssicherung

GitHub Actions führen aus:

- JSON-Validierung des QNAP-Templates
- Python- und Shell-Syntaxprüfung
- ShellCheck
- Docker-Compose-Validierung
- Gitleaks Secret-Scanning
- lokalen AMD64-Image-Build
- Healthcheck-Starttest
- Recreate-Test für persistente Managerdaten
- AMD64-/ARM64-Build mit QEMU/Buildx
- Veröffentlichung eines gemeinsamen Multi-Arch-Manifests in GHCR

Veröffentlichte Manager-Images:

```text
ghcr.io/therepro21/teslalogger-qnap-manager:1
ghcr.io/therepro21/teslalogger-qnap-manager:1.0.0
```

## Rechtliche Hinweise

- Eigener Code und Dokumentation: [MIT-Lizenz](LICENSE)
- Recht, Marken, Haftung und Datenschutz: [NOTICE.md](NOTICE.md)
- Drittkomponenten und Lizenzquellen: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)
- Sicherheitsmodell und Meldungen: [SECURITY.md](SECURITY.md)
- TeslaLogger-Upstream und GPL‑3.0: [bassmaster187/TeslaLogger](https://github.com/bassmaster187/TeslaLogger)

Fremde Namen werden ausschließlich beschreibend verwendet. Das Projektsymbol ist eigenständig und verwendet keine fremden Logos. Die Software wird ohne Gewährleistung bereitgestellt; Betrieb, Backups, Netzwerkfreigaben, Datenschutz und Einhaltung anwendbarer Vorschriften liegen in der Verantwortung des Betreibers.
