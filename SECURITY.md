# Sicherheit

Sicherheitsprobleme bitte nicht zusammen mit Zugangsdaten, Tokens oder NAS-Details in einem oeffentlichen Issue melden. Verwende stattdessen die private Sicherheitsmeldung des GitHub-Repositories unter **Security > Report a vulnerability**, sofern aktiviert.

## Sicherheitsmodell

- Das QNAP-App-Template startet einen dauerhaften Manager-Container mit Zugriff auf `/var/run/docker.sock`.
- Der Manager wird als versioniertes Multi-Arch-Image aus GHCR geladen. Anwendung und Compose-Vorlage sind im Image enthalten; beim Start wird kein ausfuehrbarer Code aus dem Internet nachgeladen.
- Der Manager benoetigt keinen privilegierten Container-Modus. Docker vergibt fuer seinen internen Port `8080` automatisch einen freien Host-Port.
- Beim ersten Start wird mit Python `secrets` ein zufaelliges Passwort erzeugt, mit Modus `0600` gespeichert und im Container-Log ausgegeben. Benutzername ist `admin`.
- Die Oberflaeche nutzt HTTP Basic Authentication und keine eigene TLS-Terminierung. Sie darf nicht direkt aus dem Internet erreichbar sein; fuer Netze ausserhalb eines vertrauenswuerdigen LAN ist ein HTTPS-Reverse-Proxy oder VPN erforderlich.
- Requests von nicht privaten, nicht lokalen Client-IP-Adressen werden mit HTTP 403 abgewiesen.
- Nur der Manager erhaelt den Docker-Socket. Die verwalteten Anwendungscontainer erhalten ihn nicht.
- Backup-Downloads erfordern die Manager-Authentifizierung. Die Archive enthalten Secrets und koennen personenbezogene Daten enthalten.
- MariaDB wird nicht als Host-Port publiziert.
- Tesla-Zugangsdaten sind niemals Bestandteil des Templates oder Installers.

Pruefe vor der Installation die Commit-Historie und verwende nur die in der README dokumentierte HTTPS-URL.
