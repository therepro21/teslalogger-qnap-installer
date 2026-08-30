# TeslaLogger QNAP Installer

> TeslaLogger mit einer einzigen App-Template-URL in QNAP Container Station 3 installieren – fuer Intel/AMD64 und ARM64, mit automatischer Portpruefung.

[![Test installer](https://github.com/therepro21/teslalogger-qnap-installer/actions/workflows/test.yml/badge.svg)](https://github.com/therepro21/teslalogger-qnap-installer/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## App-Template-URL

Diese URL in QNAP Container Station eintragen:

```text
https://raw.githubusercontent.com/therepro21/teslalogger-qnap-installer/main/qnap-template.json
```

## Installation in Container Station 3

1. **Container Station** oeffnen.
2. **Einstellungen** beziehungsweise **Preferences** waehlen.
3. Zu **App Templates** wechseln.
4. **Benutzerdefiniertes Template aktivieren** einschalten.
5. Die oben angegebene App-Template-URL einfuegen und **Anwenden** waehlen.
6. Unter **App Templates > Custom Templates** den passenden Eintrag bereitstellen:
   - `TeslaLogger QNAP Installer (Intel/AMD64)` fuer `x86_64`
   - `TeslaLogger QNAP Installer (ARM64)` fuer `aarch64`
7. Im Bereitstellungsdialog bei Bedarf Speicherpfad, Zeitzone oder Ports anpassen und den Bootstrap starten.

Der Eintrag startet einen kurzlebigen Bootstrap-Container. Dieser richtet den offiziellen TeslaLogger-Mehrcontainer-Stack ein und beendet sich danach mit Exit-Code `0`. Die eigentlichen TeslaLogger-Container laufen anschliessend getrennt weiter und erscheinen in Container Station. Der beendete Bootstrap-Container kann nach erfolgreicher Installation geloescht werden.

> **Sicherheitshinweis:** Der Bootstrap benoetigt Zugriff auf `/var/run/docker.sock`. Dieser Zugriff entspricht weitreichenden administrativen Rechten ueber Docker und den QNAP-Host. Verwende deshalb ausschliesslich die HTTPS-URL dieses Repositories und pruefe sie vor der Installation.

## Anpassbare Werte

Die folgenden Umgebungsvariablen koennen im QNAP-Bereitstellungsdialog geaendert werden:

| Variable | Standard | Bedeutung |
| --- | --- | --- |
| `TESLALOGGER_DIR` | `/share/Container/teslalogger` | Persistenter Installations- und Datenpfad |
| `TESLALOGGER_PORT` | `5010` | Host-Port fuer die TeslaLogger-API |
| `GRAFANA_PORT` | `3000` | Host-Port fuer Grafana |
| `WEBSERVER_PORT` | `8888` | Host-Port der Admin-Oberflaeche |
| `TZ` | `Europe/Berlin` | Zeitzone aller Container |

Der Standard-Bind-Mount des Templates stellt `/share/Container` bereit. Ein eigener `TESLALOGGER_DIR` muss deshalb innerhalb dieses Pfades liegen. Fuer einen anderen QNAP-Share muss im Bereitstellungsdialog zusaetzlich ein entsprechender Bind-Mount hinzugefuegt werden.

## Portkonflikte

Vor dem Start prueft der Installer:

- bereits laufende Docker-Container,
- TCP-Listener des QNAP-Hosts, wenn die Installation direkt per SSH erfolgt,
- und durch eine kurzlebige Docker-Bindprobe, ob der echte Host-Port verwendbar ist.

Ist ein Port belegt, wird automatisch der naechste freie Port innerhalb der folgenden 100 Portnummern gewaehlt. Beispiel: Ist `3000` belegt, wird `3001`, danach `3002` usw. getestet. Bei einer erneuten Installation erkennt der Installer die eigenen TeslaLogger-Container und behaelt deren Ports stabil.

| Dienst | Standard | Container-intern | Wird am Host publiziert? |
| --- | ---: | ---: | --- |
| TeslaLogger API | `5010` | `5000` | Ja |
| Grafana | `3000` | `3000` | Ja |
| Admin-Oberflaeche | `8888` | `80` | Ja |
| MariaDB | – | `3306` | **Nein** |
| Watchtower | – | – | **Nein** |

Die tatsaechlich ausgewaehlten Ports stehen nach der Installation in `/share/Container/teslalogger/.env`. Der Bootstrap zeigt sie ausserdem in seinem Container-Log an.

## Nach der Installation

Mit den tatsaechlich gewaehlten Ports erreichst du:

- Admin-Oberflaeche: `http://QNAP-IP:WEBSERVER_PORT/admin/`
- Grafana: `http://QNAP-IP:GRAFANA_PORT` – Anmeldung standardmaessig mit `admin` / `teslalogger`
- TeslaLogger API: `http://QNAP-IP:TESLALOGGER_PORT`

Die erste Initialisierung kann auf langsameren NAS-Systemen 10 bis 30 Minuten dauern. Tesla-Zugangs- beziehungsweise Fleet-API-Tokens werden erst danach in der TeslaLogger-Admin-Oberflaeche eingetragen und sind niemals Bestandteil dieses Templates.

## Verwaltung per SSH

Der Installer legt ein kleines Verwaltungsskript an:

```sh
cd /share/Container/teslalogger
./teslalogger-qnap status
./teslalogger-qnap logs
./teslalogger-qnap update
./teslalogger-qnap restart
./teslalogger-qnap stop
./teslalogger-qnap start
```

`update` laedt aktuelle Images und erstellt den Stack mit den bestehenden Einstellungen neu. Vor Aktualisierungen sollte immer ein Backup vorhanden sein.

## Alternative Installation per SSH

Falls die App-Template-Funktion nicht verfuegbar ist:

```sh
sudo -i
curl -fsSL https://raw.githubusercontent.com/therepro21/teslalogger-qnap-installer/main/install.sh | sh
```

Alternativ funktioniert auf QNAP-Systemen mit `wget`:

```sh
sudo -i
wget -qO- https://raw.githubusercontent.com/therepro21/teslalogger-qnap-installer/main/install.sh | sh
```

Eigene Werte koennen vorangestellt werden:

```sh
TESLALOGGER_DIR=/share/Container/teslalogger \
TESLALOGGER_PORT=15010 \
GRAFANA_PORT=13000 \
WEBSERVER_PORT=18888 \
TZ=Europe/Berlin \
sh install.sh
```

## Voraussetzungen und Kompatibilitaet

- QNAP mit Container Station 3 und funktionierendem Docker
- Internetzugriff auf GitHub, Docker Hub und die vom TeslaLogger-Projekt verwendeten Registries
- 64-Bit Intel/AMD (`x86_64`) oder 64-Bit ARM (`aarch64`)
- Schreibbarer QNAP-Share fuer persistente Daten

32-Bit ARM wird nicht angeboten, weil die von TeslaLogger verwendete MariaDB-Konfiguration ein 64-Bit-System voraussetzt. Auf ARM64 aktiviert der Installer den aktuell benoetigten Workaround fuer die SkiaSharp-Kartengenerierung.

Die bei Erstellung dieses Templates verwendeten Images wurden auf vorhandene `linux/amd64`- und `linux/arm64`-Manifeste geprueft: TeslaLogger, TeslaLogger Grafana, TeslaLogger Webserver, MariaDB `10.4.7`, Watchtower und der Docker-CLI-Bootstrap. Da mehrere Upstream-Images den beweglichen Tag `latest` verwenden, wird diese Kompatibilitaet bei spaeteren Upstream-Aenderungen nicht garantiert; vor produktiven Updates sollte ein Backup erstellt werden.

## Funktionsweise

Das QNAP-App-Templateformat beschreibt einzelne Container, TeslaLogger besteht jedoch aus mehreren Diensten. Deshalb verwendet dieses Projekt einen einmaligen Bootstrap:

1. Container Station startet das versionsgebundene offizielle Multi-Arch-Image `docker:29.7.2-cli`.
2. Das Template bindet den Docker-Socket und `/share/Container` ein.
3. Der Bootstrap laedt den oeffentlichen Installer aus diesem Repository.
4. Der Installer prueft Architektur, Speicherpfad und Ports.
5. Die aktuelle offizielle TeslaLogger-Konfiguration aus dem Zweig `NET8` wird geladen.
6. Docker Compose startet TeslaLogger, MariaDB, Grafana, Webserver und Watchtower.
7. Der Bootstrap beendet sich; der TeslaLogger-Stack laeuft weiter.

Dieses Repository enthaelt keinen TeslaLogger-Quellcode und keine Tesla-Zugangsdaten.

## Fehlerbehebung

### Template erscheint nicht

- Pruefen, ob die Raw-URL im Browser ohne Anmeldung erreichbar ist.
- Container Station nach einer Template-Aenderung neu laden.
- Sicherstellen, dass Container Station 3 verwendet wird.

### Bootstrap endet mit Fehler

- In Container Station das Log des Bootstrap-Containers oeffnen.
- Pruefen, ob `/var/run/docker.sock` und `/share/Container` eingebunden wurden.
- Pruefen, ob GitHub und Docker Hub vom NAS erreichbar sind.

### Oberflaeche ist nicht erreichbar

- Die tatsaechlichen Ports im Bootstrap-Log oder in `.env` pruefen.
- Den Stackstatus mit `./teslalogger-qnap status` kontrollieren.
- Bei der Erstinstallation bis zu 30 Minuten warten und `./teslalogger-qnap logs` ansehen.
- QNAP-Firewall- beziehungsweise QuFirewall-Regeln pruefen.

## Recht, Marken und Haftung

Dieses Projekt ist ein **inoffizielles Community-Projekt** und weder mit Tesla, TeslaLogger, QNAP Systems, Docker, MariaDB noch Grafana Labs verbunden oder von diesen geprueft. Produktnamen werden ausschliesslich zur Beschreibung der Kompatibilitaet verwendet.

- Projektcode und Dokumentation: [MIT-Lizenz](LICENSE)
- Ausfuehrliche rechtliche Hinweise: [NOTICE.md](NOTICE.md)
- Drittkomponenten und deren Lizenzquellen: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)
- Sicherheitsmodell und Meldungen: [SECURITY.md](SECURITY.md)
- TeslaLogger-Upstream: [bassmaster187/TeslaLogger](https://github.com/bassmaster187/TeslaLogger)

Die Software wird ohne Gewaehrleistung bereitgestellt. Betrieb, Datensicherung, Netzwerksicherheit, Datenschutz und die Einhaltung anwendbarer Vorschriften liegen in der Verantwortung des Betreibers.

## Mitwirken

Fehlerberichte und Pull Requests sind willkommen. Bitte niemals Tesla-Tokens, NAS-Zugangsdaten, oeffentliche IP-Adressen oder vollstaendige Logdateien mit Geheimnissen in Issues veroeffentlichen.
