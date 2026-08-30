# Hinweise zu Drittkomponenten

Dieses Projekt automatisiert die Installation, enthaelt aber keinen Quellcode der folgenden Drittprojekte. Versionen und Lizenzbedingungen koennen sich bei `latest`-Images oder Updates aendern. Vor produktivem Einsatz sind die jeweils aktuellen Image-Metadaten und Lizenztexte zu pruefen.

| Komponente | Verwendung | Projekt/Lizenzhinweis |
| --- | --- | --- |
| TeslaLogger | Hauptanwendung und offizielle Compose-Konfiguration | [Upstream-Repository](https://github.com/bassmaster187/TeslaLogger), dort als GPL-3.0 ausgewiesen |
| Docker CLI Image | Kurzlebiger QNAP-Bootstrap und Compose-Client | [Official Image](https://hub.docker.com/_/docker), Komponenten mit eigenen Open-Source-Lizenzen |
| MariaDB | Datenbank im offiziellen TeslaLogger-Stack | [MariaDB Licensing](https://mariadb.com/kb/en/mariadb-licensing/) |
| Grafana | Visualisierung im offiziellen TeslaLogger-Stack | [Grafana Licensing](https://grafana.com/licensing/) |
| Watchtower | Automatisierte Container-Aktualisierung im offiziellen Stack | [Watchtower Repository](https://github.com/containrrr/watchtower) |
| QNAP Container Station | Zielplattform | Proprietaere Software von QNAP Systems, Inc. |

Die Aufnahme in diese Liste bedeutet nicht, dass die jeweiligen Rechteinhaber dieses Projekt unterstuetzen oder geprueft haben.
