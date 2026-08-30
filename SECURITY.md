# Sicherheit

Sicherheitsprobleme bitte nicht zusammen mit Zugangsdaten, Tokens oder NAS-Details in einem oeffentlichen Issue melden. Verwende stattdessen die private Sicherheitsmeldung des GitHub-Repositories unter **Security > Report a vulnerability**, sofern aktiviert.

## Sicherheitsmodell

- Das QNAP-App-Template startet einen einmaligen Bootstrap-Container mit Zugriff auf `/var/run/docker.sock`.
- Der Bootstrap laedt `install.sh` ausschliesslich aus diesem GitHub-Repository und startet den offiziellen TeslaLogger-Compose-Stack.
- Der Bootstrap benoetigt keinen privilegierten Container-Modus und veroeffentlicht selbst keine Ports.
- MariaDB wird nicht als Host-Port publiziert.
- Tesla-Zugangsdaten sind niemals Bestandteil des Templates oder Installers.

Pruefe vor der Installation die Commit-Historie und verwende nur die in der README dokumentierte HTTPS-URL.
