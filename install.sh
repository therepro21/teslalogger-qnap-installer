#!/bin/sh
set -eu

REPO_BRANCH="${TESLALOGGER_BRANCH:-NET8}"
INSTALL_DIR="${TESLALOGGER_DIR:-/share/Container/teslalogger}"
UPSTREAM="https://raw.githubusercontent.com/bassmaster187/TeslaLogger/refs/heads/${REPO_BRANCH}"

say() { printf '\n[teslalogger-qnap] %s\n' "$*"; }
die() { printf '\n[teslalogger-qnap] FEHLER: %s\n' "$*" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }

[ "$(id -u)" -eq 0 ] || die "Bitte als Administrator ausfuehren (sudo -i)."

ARCH="$(uname -m)"
case "$ARCH" in
  x86_64|amd64) PLATFORM="linux/amd64" ;;
  aarch64|arm64) PLATFORM="linux/arm64" ;;
  armv7l|armv6l|arm) die "32-Bit ARM wird von der benoetigten MariaDB-Version nicht unterstuetzt. Erforderlich ist ARM64." ;;
  *) die "Nicht unterstuetzte Architektur: $ARCH (unterstuetzt: x86_64 und aarch64)." ;;
esac

have docker || die "Docker wurde nicht gefunden. Bitte QNAP Container Station installieren und starten."
if docker compose version >/dev/null 2>&1; then
  COMPOSE="docker compose"
elif have docker-compose && docker-compose version >/dev/null 2>&1; then
  COMPOSE="docker-compose"
else
  die "Docker Compose wurde nicht gefunden. Bitte Container Station aktualisieren."
fi

if have curl; then
  fetch() { curl -fsSL --retry 3 "$1" -o "$2"; }
elif have wget; then
  fetch() { wget -q "$1" -O "$2"; }
else
  die "curl oder wget wird zum Download benoetigt."
fi

say "Architektur: $ARCH ($PLATFORM)"
say "Installationsordner: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR/backup" "$INSTALL_DIR/invoices" "$INSTALL_DIR/mysql"
# Die Container laufen nicht zwingend mit der QNAP-Host-UID. Das entspricht
# der offiziellen TeslaLogger-Docker-Anleitung und verhindert Schreibfehler.
chmod 777 "$INSTALL_DIR/backup" "$INSTALL_DIR/invoices" "$INSTALL_DIR/mysql"
cd "$INSTALL_DIR"

say "Lade die aktuelle offizielle TeslaLogger-NET8-Konfiguration ..."
fetch "$UPSTREAM/docker-compose.yml" "docker-compose.yml.new"
fetch "$UPSTREAM/.env" ".env.upstream"
[ -s docker-compose.yml.new ] || die "Die Compose-Datei konnte nicht geladen werden."
mv docker-compose.yml.new docker-compose.yml

if [ ! -f .env ]; then
  cp .env.upstream .env
fi

set_env() {
  key="$1"; value="$2"; file=".env"
  if grep -q "^${key}=" "$file"; then
    sed "s|^${key}=.*|${key}=${value}|" "$file" > "$file.tmp" && mv "$file.tmp" "$file"
  else
    printf '%s=%s\n' "$key" "$value" >> "$file"
  fi
}
set_env APPDATA_PATH "$INSTALL_DIR"
set_env TZ "${TZ:-Europe/Berlin}"

cat > docker-compose.qnap.yml <<EOF
services:
  teslalogger:
    platform: ${PLATFORM}
EOF

if [ "$PLATFORM" = "linux/arm64" ]; then
  cat >> docker-compose.qnap.yml <<'EOF'
    environment:
      LD_PRELOAD: /usr/lib/aarch64-linux-gnu/libfreetype.so.6:/usr/lib/aarch64-linux-gnu/libuuid.so.1
EOF
fi

cat > teslalogger-qnap <<'EOF'
#!/bin/sh
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
if docker compose version >/dev/null 2>&1; then C="docker compose"; else C="docker-compose"; fi
case "${1:-status}" in
  start)   $C -f docker-compose.yml -f docker-compose.qnap.yml up -d ;;
  stop)    $C -f docker-compose.yml -f docker-compose.qnap.yml stop ;;
  restart) $C -f docker-compose.yml -f docker-compose.qnap.yml restart ;;
  update)  $C -f docker-compose.yml -f docker-compose.qnap.yml pull && $C -f docker-compose.yml -f docker-compose.qnap.yml up -d ;;
  logs)    $C -f docker-compose.yml -f docker-compose.qnap.yml logs -f --tail=200 ;;
  status)  $C -f docker-compose.yml -f docker-compose.qnap.yml ps ;;
  *) echo "Aufruf: $0 {start|stop|restart|update|logs|status}" >&2; exit 2 ;;
esac
EOF
chmod 755 teslalogger-qnap

say "Pruefe Compose-Konfiguration ..."
# shellcheck disable=SC2086
$COMPOSE -f docker-compose.yml -f docker-compose.qnap.yml config >/dev/null
say "Lade Images und starte TeslaLogger ..."
# shellcheck disable=SC2086
$COMPOSE -f docker-compose.yml -f docker-compose.qnap.yml pull
# shellcheck disable=SC2086
$COMPOSE -f docker-compose.yml -f docker-compose.qnap.yml up -d

IP="$(hostname -I 2>/dev/null | awk '{print $1}' || true)"
[ -n "$IP" ] || IP="QNAP-IP"
say "Fertig. Die Erstinitialisierung kann 10-30 Minuten dauern."
printf 'Admin:   http://%s:8888/admin/\n' "$IP"
printf 'Grafana: http://%s:3000  (admin / teslalogger)\n' "$IP"
printf 'Status:  %s/teslalogger-qnap status\n' "$INSTALL_DIR"
