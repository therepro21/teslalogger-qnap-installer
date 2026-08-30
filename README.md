# TeslaLogger QNAP Installer

Ein Einzeiler-Installer fuer [TeslaLogger](https://github.com/bassmaster187/TeslaLogger) in QNAP Container Station. Unterstuetzt 64-Bit Intel/AMD (`x86_64`) und 64-Bit ARM (`aarch64`).

> 32-Bit-ARM-QNAPs werden nicht unterstuetzt, weil die von TeslaLogger benoetigte MariaDB-Version ein 64-Bit-System voraussetzt.

## Installation

1. Container Station auf dem QNAP installieren und starten.
2. In QTS unter **Systemsteuerung > Netzwerk & Dateidienste > Telnet/SSH** SSH aktivieren.
3. Per SSH anmelden, Administrator-Shell oeffnen und den Einzeiler ausfuehren.

Da dieses Repository privat ist, benoetigt der GitHub-Aufruf ein Fine-grained Personal Access Token mit Leserechten fuer dieses Repository:

```sh
sudo -i
read -s -p "GitHub Token: " GITHUB_TOKEN; echo; export GITHUB_TOKEN
curl -fsSL -H "Authorization: Bearer $GITHUB_TOKEN" -H "Accept: application/vnd.github.raw+json" \
  https://api.github.com/repos/therepro21/teslalogger-qnap-installer/contents/install.sh | sh
unset GITHUB_TOKEN
```

Alternativ als einzelner kopierbarer Befehl (Token wird dabei in der Shell-History gespeichert):

```sh
GITHUB_TOKEN='HIER_TOKEN_EINSETZEN' sh -c 'curl -fsSL -H "Authorization: Bearer $GITHUB_TOKEN" -H "Accept: application/vnd.github.raw+json" https://api.github.com/repos/therepro21/teslalogger-qnap-installer/contents/install.sh | sh'
```

Die Daten landen standardmaessig dauerhaft unter `/share/Container/teslalogger`. Ein anderer Pfad kann vorgegeben werden:

```sh
TESLALOGGER_DIR=/share/MeinShare/teslalogger sh install.sh
```

## Ports und automatische Konfliktpruefung

Der Installer prueft vor dem Start sowohl laufende Docker-Container als auch andere TCP-Dienste auf dem QNAP. Bereits von diesem TeslaLogger-Stack verwendete Ports bleiben bei einer erneuten Installation unveraendert. Ist ein gewuenschter Port durch Container Station, QTS oder eine andere Anwendung belegt, waehlt der Installer automatisch den naechsten freien Port innerhalb der folgenden 100 Ports und speichert ihn in `.env`.

| Dienst | Standardport | Container-Port | Beispiel bei Konflikt |
| --- | ---: | ---: | ---: |
| TeslaLogger API | `5010` | `5000` | `5011` |
| Grafana | `3000` | `3000` | `3001` |
| Admin-Oberflaeche | `8888` | `80` | `8889` |

MariaDB wird bewusst **nicht** auf dem QNAP-Host veroeffentlicht. Port `3306` bleibt ausschliesslich innerhalb des Docker-Netzwerks erreichbar. Watchtower veroeffentlicht ebenfalls keinen Host-Port.

Eigene Wunschports koennen beim Aufruf vorgegeben werden:

```sh
TESLALOGGER_PORT=15010 GRAFANA_PORT=13000 WEBSERVER_PORT=18888 sh install.sh
```

Sind Wunschports belegt, gilt dieselbe automatische Suche. Die am Ende angezeigten URLs enthalten immer die tatsaechlich ausgewaehlten Ports. Sie stehen danach auch in `/share/Container/teslalogger/.env`.

## Bedienung

```sh
cd /share/Container/teslalogger
./teslalogger-qnap status
./teslalogger-qnap logs
./teslalogger-qnap update
./teslalogger-qnap restart
./teslalogger-qnap stop
./teslalogger-qnap start
```

- Admin-Oberflaeche: `http://QNAP-IP:WEBSERVER_PORT/admin/`
- Grafana: `http://QNAP-IP:GRAFANA_PORT` (`admin` / `teslalogger`)
- TeslaLogger API: `http://QNAP-IP:TESLALOGGER_PORT`
- Die konkreten Portnummern zeigt der Installer nach erfolgreichem Start an und speichert sie in `.env`.
- Die Erstinitialisierung kann auf einem NAS 10 bis 30 Minuten dauern.

## Sicherheit und Hinweise

- Der Installer uebertraegt keine Tesla-Zugangsdaten. Tokens werden spaeter direkt in TeslaLogger eingetragen.
- Das GitHub-Token wird nicht gespeichert. Nach dem Download wird es mit `unset GITHUB_TOKEN` aus der Sitzung entfernt.
- Bestehende `.env`-Einstellungen bleiben bei erneuter Installation erhalten.
- Vor jedem Start werden Portkonflikte mit Docker-Containern und QNAP-Hostdiensten geprueft. Ein laufender eigener TeslaLogger-Stack wird korrekt erkannt und behaelt seine Ports.
- Der Installer setzt auf ARM64 den derzeit notwendigen `libSkiaSharp`-Workaround fuer die Kartengenerierung.
- Container Station zeigt die gestarteten Docker-Container automatisch an.

## Quelle

Compose-Datei und Standardkonfiguration werden bei der Installation direkt aus dem offiziellen TeslaLogger-Zweig `NET8` geladen. Dieses Repository enthaelt keinen TeslaLogger-Code.
