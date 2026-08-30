# Rechtliche Hinweise

## Eigenstaendiges Community-Projekt

Dieses Repository ist ein inoffizielles, eigenstaendiges Community-Projekt. Es besteht keine Verbindung, Partnerschaft, Zertifizierung oder Billigung durch Tesla, TeslaLogger, QNAP Systems, Docker, MariaDB, Grafana Labs oder die jeweiligen Rechteinhaber.

`Tesla`, `TeslaLogger`, `QNAP`, `Container Station`, `Docker`, `MariaDB`, `Grafana` sowie weitere Produkt- und Unternehmensnamen koennen Marken ihrer jeweiligen Inhaber sein. Ihre Nennung dient ausschliesslich der Beschreibung von Kompatibilitaet und Verwendungszweck.

## Lizenzen

- Der in diesem Repository enthaltene Installer, das QNAP-Template, die Dokumentation und das projektspezifische Symbol stehen unter der [MIT-Lizenz](LICENSE).
- TeslaLogger wird nicht in diesem Repository weitergegeben. Der Installer laedt Konfiguration und Container-Images aus den vom TeslaLogger-Projekt angegebenen Quellen. TeslaLogger steht nach Angabe des Upstream-Projekts unter der GNU General Public License v3.0. Massgeblich sind stets die Lizenztexte und Hinweise des jeweiligen Upstream-Projekts.
- Verwendete Container-Images und darin enthaltene Komponenten unterliegen ihren eigenen Lizenzen. Eine Uebersicht befindet sich in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Haftung und Betrieb

Die Software wird ohne Gewaehrleistung bereitgestellt. Der Betrieb erfolgt auf eigenes Risiko. Vor Installation und Aktualisierung sollten vollstaendige Sicherungen des QNAP und der TeslaLogger-Daten angelegt werden. Der Betreiber ist selbst fuer Netzwerkfreigaben, Firewallregeln, Zugangsdaten, Datenschutz, Datensicherung, Updates und die Einhaltung der fuer ihn geltenden Vorschriften verantwortlich.

Das Template bindet `/var/run/docker.sock` in einen kurzlebigen Bootstrap-Container ein. Zugriff auf diesen Socket entspricht weitreichenden administrativen Rechten ueber Docker und den QNAP-Host. Das Template sollte deshalb ausschliesslich aus der in der README angegebenen Repository-URL geladen und vor der Verwendung geprueft werden.

## Datenschutz

Dieser Installer erhebt und versendet selbst keine Telemetrie und fordert keine Tesla-Zugangsdaten an. Tesla-Zugangs- oder Fleet-API-Tokens werden spaeter in der von TeslaLogger bereitgestellten Oberflaeche hinterlegt. Fuer die Datenverarbeitung durch TeslaLogger und eingebundene Dienste gelten deren Dokumentation und Datenschutzinformationen.
