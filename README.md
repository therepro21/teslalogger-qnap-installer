# TeslaLogger QNAP Manager

Eine vollständig klickbare Installation und Verwaltung von [TeslaLogger](https://github.com/bassmaster187/TeslaLogger) für QNAP Container Station 3 – ohne SSH, ohne Bash und ohne manuell gepflegte Compose-Dateien.

[![Validate, test and publish](https://github.com/therepro21/teslalogger-qnap-installer/actions/workflows/ci.yml/badge.svg)](https://github.com/therepro21/teslalogger-qnap-installer/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> Inoffizielles Community-Projekt; nicht verbunden mit oder unterstützt von Tesla, TeslaLogger, QNAP Systems, Docker, MariaDB oder Grafana Labs.

**Sprachen / Languages:** [Deutsch](#deutsch-klick-für-klick) · [English](#english-click-by-click)

## QNAP-App-Template-URL

Diese öffentliche URL wird direkt in Container Station 3 eingetragen:

```text
https://raw.githubusercontent.com/therepro21/teslalogger-qnap-installer/main/qnap-template.json
```

## Deutsch: Klick für Klick

### Vorher prüfen

1. In QTS **Systemsteuerung > Systemstatus > Systeminformationen** öffnen und bei **CPU** nachsehen:
   - Intel oder AMD sowie `x86_64` → Template **Intel/AMD64**.
   - ARM-Prozessor sowie `aarch64` oder `ARMv8` → Template **ARM64**.
   - `ARMv7`, `armhf`, 32 Bit oder MIPS → nicht unterstützt; nicht versuchsweise das andere Template verwenden.
2. Die lokale QNAP-IP in **Systemsteuerung > Netzwerk & virtueller Switch > Netzwerk > Schnittstellen** notieren, zum Beispiel `192.168.1.50`.
3. Container Station 3 muss aus dem QNAP App Center installiert und gestartet sein.

### Template in Container Station eintragen

1. Im QNAP App Center **Container Station 3** installieren und öffnen.
2. Links oder oben rechts das Zahnrad **Einstellungen / Preferences** öffnen. Je nach QTS-Version kann es **Preferences > App Templates** heißen.
3. **App Templates / Anwendungsvorlagen** auswählen.
4. **Benutzerdefiniertes Template aktivieren / Enable custom template** einschalten.
5. In das Feld **Template URL** exakt diese vollständige Adresse einfügen (nicht die normale GitHub-Seite):

   ```text
   https://raw.githubusercontent.com/therepro21/teslalogger-qnap-installer/main/qnap-template.json
   ```

6. **Anwenden / Apply** anklicken. Erscheint „ungültige URL“, Leerzeichen vor oder hinter der URL entfernen und prüfen, ob die QNAP Internetzugang zu `raw.githubusercontent.com` hat.
7. Zu **App Templates > Custom Templates / Benutzerdefiniert** wechseln. Falls nichts erscheint, die Ansicht einmal aktualisieren.
8. Das zur QNAP-CPU passende Template wählen:
   - **TeslaLogger QNAP Manager (Intel/AMD64)** für `x86_64`
   - **TeslaLogger QNAP Manager (ARM64)** für `aarch64`
9. **Deploy / Bereitstellen**, danach **Weiter** und **Fertigstellen** anklicken. Die vorgeschlagenen beiden Volumes und den Docker-Socket nicht entfernen. **Privileged / Privilegiert** bleibt ausgeschaltet.
10. Unter **Container** warten, bis `teslalogger-qnap-manager` als **Running / Wird ausgeführt** angezeigt wird.
11. Den Manager anklicken und **Details > Portweiterleitung / Port forwarding** öffnen. Neben Container-Port `8080/tcp` steht der automatisch gewählte **Host-Port**, beispielsweise `32781`. Diese Zahl notieren. Sie ist nicht der spätere TeslaLogger-Port.
12. Im selben Container **Protokolle / Logs** öffnen. Nach `Manager password:` suchen und nur das dahinter stehende Passwort kopieren. Es bleibt dauerhaft im geschützten Manager-Volume gespeichert.
13. Im Browser `http://QNAP-IP:HOST-PORT` öffnen, beispielsweise `http://192.168.1.50:32781`.
14. Mit Benutzer `admin` und dem Passwort aus dem Container-Log anmelden.
15. Bei jedem Feld zuerst auf das kleine **?** klicken. Für eine typische Installation im Heimnetz gelten meistens diese Werte:
   - Bind-IP: `0.0.0.0`
   - TeslaLogger-Port: `5010`
   - Grafana-Port: `3000`
   - Admin-Port: `8888`
   - Zeitzone: `Europe/Berlin` (Deutschland/Österreich) oder `Europe/Zurich` (Schweiz)
   - Domain: leer
   - Schema: `http`
16. **Ports prüfen & anwenden** anklicken. Der Helfer prüft auch Ports anderer Grafana-, MariaDB- oder QNAP-Dienste. Bei einer Belegung wird automatisch ein freier Folgeport gewählt und angezeigt.
17. Warten, bis unter **Letzter Vorgang** der Abschluss gemeldet wird. Erststart und Datenbankinitialisierung können 10–30 Minuten dauern.
18. Die oben im Manager angezeigten Links öffnen. Für die meisten lokalen Installationen sind das anschließend ungefähr `http://QNAP-IP:8888/admin/` und `http://QNAP-IP:3000`.

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

| Einstellung | Meistens/Standard | Wo finde ich den Wert? | Bedeutung |
| --- | --- | --- | --- |
| Interne Bind-IP | `0.0.0.0` | QTS: **Systemsteuerung > Netzwerk & virtueller Switch > Schnittstellen** | `0.0.0.0` bedeutet alle lokalen QNAP-Schnittstellen. Eine konkrete IP nur bei mehreren LAN-Ports/VLANs verwenden. |
| TeslaLogger-Port | `5010` | Frei wählbar; bestehende Belegungen in **Container Station > Container > Details > Ports** | Externer Host-Port des TeslaLogger-Dienstes, intern bleibt es `5000`. |
| Grafana-Port | `3000` | Wie oben; 3000 ist der übliche Grafana-Port | Browserzugang zu Grafana. Eine vorhandene Grafana-Instanz bleibt unverändert; der Helfer wählt dann z. B. 3001. |
| Admin-Port | `8888` | Wie oben | TeslaLogger-Adminoberfläche, intern Port `80`. Nicht mit dem dynamischen Manager-Port verwechseln. |
| Zeitzone | `Europe/Berlin` | Nach Region/Stadt; DE/AT `Europe/Berlin`, CH `Europe/Zurich` | Uhrzeiten in Anwendung, Grafana, Logs und Backups einschließlich Sommerzeit. |
| Domain / externe IP | leer | Domain beim DNS-Anbieter; Reverse Proxy in QTS unter **Systemsteuerung > Anwendungen > Reverse Proxy** | Nur Hostname, z. B. `teslalogger.example.de`; kein Schema, Pfad oder Port. Für reinen LAN-Betrieb leer lassen. |
| Schema | `http` lokal, `https` mit Proxy | Abhängig davon, ob im Reverse Proxy ein gültiges TLS-Zertifikat eingerichtet ist | Ändert die angezeigten externen Links, richtet aber selbst kein HTTPS ein. |

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

## English: click by click

### Before you start

1. Open QTS **Control Panel > System Status > System Information** and check **CPU**:
   - Intel/AMD or `x86_64`: select the **Intel/AMD64** template.
   - ARM with `aarch64` or `ARMv8`: select the **ARM64** template.
   - ARMv7, `armhf`, 32-bit ARM and MIPS are not supported. Do not try the other template as a workaround.
2. Note the QNAP's LAN address from **Control Panel > Network & Virtual Switch > Network > Interfaces**, for example `192.168.1.50`.
3. Install and start Container Station 3 from QNAP App Center.

### Add and deploy the template

1. Open Container Station 3 and select the gear icon **Preferences**.
2. Open **App Templates** and enable **Custom templates**.
3. Paste this complete Raw GitHub URL into **Template URL** (not the normal GitHub repository page):

   ```text
   https://raw.githubusercontent.com/therepro21/teslalogger-qnap-installer/main/qnap-template.json
   ```

4. Select **Apply**. If QNAP reports an invalid URL, remove surrounding spaces and verify that the NAS can reach `raw.githubusercontent.com`.
5. Open **App Templates > Custom Templates** and refresh once if the list is initially empty.
6. Select **TeslaLogger QNAP Manager (Intel/AMD64)** for x86-64 or **TeslaLogger QNAP Manager (ARM64)** for ARM64.
7. Select **Deploy**, continue through the review and select **Finish**. Keep both proposed volumes and the Docker socket mapping. Do not enable **Privileged** mode.
8. Open **Containers** and wait for `teslalogger-qnap-manager` to show **Running**.
9. Open that container's **Details > Port forwarding**. Note the automatically assigned **host port** next to container port `8080/tcp`, for example `32781`.
10. Open **Logs**, find `Manager password:` and copy the value after it.
11. Browse to `http://QNAP-IP:HOST-PORT`, for example `http://192.168.1.50:32781`, and sign in as `admin` with the logged password.
12. Click the small **?** beside every setting. A normal home-network installation usually uses:
    - Internal bind IP: `0.0.0.0`
    - TeslaLogger port: `5010`
    - Grafana port: `3000`
    - Admin port: `8888`
    - Time zone: e.g. `Europe/Berlin`, `Europe/Zurich` or your own Region/City value
    - Domain: empty
    - Scheme: `http`
13. Select **Check ports & apply**. The helper checks Docker and non-Docker port conflicts and automatically chooses a free following port when necessary.
14. Wait for the final operation message. Initial database and application startup may take 10–30 minutes on slower NAS hardware.
15. Use the Admin and Grafana links shown by the manager. Typical local addresses are `http://QNAP-IP:8888/admin/` and `http://QNAP-IP:3000`.

### What each setting means

| Setting | Usually | Where to find or choose it | Meaning |
| --- | --- | --- | --- |
| Internal bind IP | `0.0.0.0` | QTS **Control Panel > Network & Virtual Switch > Interfaces** | Exposes the application on all local NAS interfaces. Use one exact QNAP IP only for a deliberate multi-interface/VLAN restriction. |
| TeslaLogger port | `5010` | Choose a free port; existing mappings are under **Container Station > Containers > Details > Ports** | QNAP host port for the TeslaLogger service; the internal port remains `5000`. |
| Grafana port | `3000` | Same location; 3000 is Grafana's common default | Browser access to Grafana. An existing Grafana is not changed; the helper can select 3001 or another free port. |
| Admin port | `8888` | Same location | TeslaLogger's admin website; internal port `80`. This is not the dynamically assigned manager port. |
| Time zone | your `Region/City` | Common examples: `Europe/Berlin`, `Europe/Zurich`, `America/New_York` | Controls local timestamps and daylight-saving behavior in TeslaLogger, Grafana, logs and backups. |
| Domain / external IP | empty for LAN use | Domain at your DNS provider; reverse proxy in QTS **Control Panel > Applications > Reverse Proxy** | Enter only a hostname such as `teslalogger.example.com`, without scheme, path or port. |
| External scheme | `http` on LAN; `https` behind TLS proxy | Depends on your reverse proxy and certificate | Controls displayed external links. It does not create DNS, HTTPS or a certificate. |

### Existing Grafana, MariaDB and port conflicts

The helper inspects published Docker ports and performs a real bind test that also detects QTS and other non-container services. If port 3000 is already occupied by another Grafana, it tries 3001, 3002 and so on, without changing the existing service. The included MariaDB does not publish host port 3306 and therefore does not conflict with another MariaDB container or QNAP database service.

### Updates, backup, domain changes and removal

- Use **Backup & Update** in the manager. It creates a backup before pulling images and replaces only containers, reusing all persistent volumes.
- Use **Create backup** to generate a downloadable archive. Restore requires the exact confirmation `RESTORE` and first creates another safety backup.
- To change a domain, reopen the manager, change **Domain** and **Scheme**, apply, then update DNS, QNAP reverse proxy and certificate separately.
- **Remove containers, keep data** preserves every volume. Permanent removal requires the exact confirmation `ALLE DATEN LOESCHEN` and creates a final backup first.
- Never expose the manager's dynamically assigned port to the Internet. Prefer VPN for manager access. The Docker socket gives the manager Docker-host-level control.

### Persistent volumes — never delete during an update or rebuild

`teslalogger_qnap_manager_data`, `teslalogger_qnap_backups`, `teslalogger_qnap_mysql`, `teslalogger_qnap_data`, `teslalogger_qnap_app_backup`, `teslalogger_qnap_invoices`, `teslalogger_qnap_grafana`, `teslalogger_qnap_grafana_dashboards`, `teslalogger_qnap_grafana_plugins`, `teslalogger_qnap_sqlschema`, and `teslalogger_qnap_tmp`.

This is an unofficial community project and is not affiliated with or endorsed by Tesla, TeslaLogger, QNAP Systems, Docker, MariaDB or Grafana Labs. See [LICENSE](LICENSE), [NOTICE.md](NOTICE.md), [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and [SECURITY.md](SECURITY.md).

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
