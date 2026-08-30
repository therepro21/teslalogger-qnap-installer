#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 therepro21
"""Browser-based lifecycle manager for TeslaLogger on QNAP Container Station 3."""

from __future__ import annotations

import base64
import html
import ipaddress
import json
import os
import platform
import re
import secrets
import shutil
import subprocess
import tarfile
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote

APP_DIR = Path("/opt/teslalogger-qnap-manager")
DATA_DIR = Path(os.environ.get("MANAGER_DATA", "/manager-data"))
BACKUP_DIR = Path(os.environ.get("BACKUP_DIR", "/backups"))
COMPOSE_FILE = DATA_DIR / "compose.yaml"
ENV_FILE = DATA_DIR / ".env"
CONFIG_FILE = DATA_DIR / "config.json"
SECRETS_FILE = DATA_DIR / "secrets.json"
TOKEN_FILE = DATA_DIR / ".manager-token"
PORT = int(os.environ.get("MANAGER_PORT", "8080"))
STACK = os.environ.get("STACK_NAME", "teslalogger-qnap")
ALPINE_IMAGE = "alpine:3.22"
SUPPORTED_ARCH = {"x86_64": "linux/amd64", "amd64": "linux/amd64", "aarch64": "linux/arm64", "arm64": "linux/arm64"}
PROTECTED_VOLUMES = [
    "teslalogger_qnap_mysql",
    "teslalogger_qnap_data",
    "teslalogger_qnap_app_backup",
    "teslalogger_qnap_invoices",
    "teslalogger_qnap_grafana",
    "teslalogger_qnap_grafana_dashboards",
    "teslalogger_qnap_grafana_plugins",
    "teslalogger_qnap_sqlschema",
    "teslalogger_qnap_tmp",
]
ARCHIVE_VOLUMES = [volume for volume in PROTECTED_VOLUMES if volume != "teslalogger_qnap_mysql"]
DEFAULT_CONFIG = {
    "BIND_IP": "0.0.0.0",
    "TESLALOGGER_PORT": "5010",
    "GRAFANA_PORT": "3000",
    "WEBSERVER_PORT": "8888",
    "TZ": os.environ.get("TZ", "Europe/Berlin"),
    "PUBLIC_SCHEME": "http",
    "PUBLIC_HOST": "",
    "TESLALOGGER_IMAGE": "bassmaster187/teslalogger:latest",
    "GRAFANA_IMAGE": "bassmaster187/teslalogger-grafana:latest",
    "WEBSERVER_IMAGE": "bassmaster187/teslalogger-webserver:latest",
}

DATA_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def atomic_write(path: Path, value: str, mode: int = 0o600) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(value, encoding="utf-8")
    temporary.chmod(mode)
    temporary.replace(path)


def load_json(path: Path, fallback: dict[str, str]) -> dict[str, str]:
    if not path.exists():
        return dict(fallback)
    loaded = json.loads(path.read_text(encoding="utf-8"))
    return {**fallback, **{str(key): str(value) for key, value in loaded.items()}}


def save_json(path: Path, value: dict[str, str]) -> None:
    atomic_write(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def secret_file(path: Path, key: str) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    value = secrets.token_urlsafe(32)
    atomic_write(path, value + "\n")
    return value


TOKEN = secret_file(TOKEN_FILE, "manager")
SECRETS = load_json(SECRETS_FILE, {})
for secret_name in ("DB_PASSWORD", "DB_ROOT_PASSWORD", "GRAFANA_PASSWORD"):
    SECRETS.setdefault(secret_name, secrets.token_urlsafe(32))
save_json(SECRETS_FILE, SECRETS)

CONFIG = load_json(CONFIG_FILE, DEFAULT_CONFIG)
save_json(CONFIG_FILE, CONFIG)
shutil.copy2(APP_DIR / "compose.yaml", COMPOSE_FILE)
COMPOSE_FILE.chmod(0o600)

job_lock = threading.Lock()
job_state: dict[str, object] = {"running": False, "title": "Bereit", "output": "", "ok": True}


def run(command: list[str], *, timeout: int = 600, stdin: bytes | None = None, check: bool = True) -> str:
    result = subprocess.run(
        command, input=stdin, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        timeout=timeout, check=False
    )
    output = result.stdout.decode("utf-8", errors="replace")
    if check and result.returncode != 0:
        raise RuntimeError(f"Befehl fehlgeschlagen ({result.returncode}): {' '.join(command)}\n{output[-12000:]}")
    return output


def docker(*args: str, timeout: int = 600, check: bool = True) -> str:
    return run(["docker", *args], timeout=timeout, check=check)


def compose(*args: str, timeout: int = 1200, check: bool = True) -> str:
    return run([
        "docker", "compose", "--project-name", STACK, "--env-file", str(ENV_FILE),
        "--file", str(COMPOSE_FILE), *args
    ], timeout=timeout, check=check)


def validate_architecture() -> str:
    machine = platform.machine().lower()
    if machine not in SUPPORTED_ARCH:
        raise RuntimeError(f"Nicht unterstuetzte Architektur: {machine}. Unterstuetzt werden nur x86_64/amd64 und aarch64/arm64.")
    return SUPPORTED_ARCH[machine]


def validate_config(candidate: dict[str, str]) -> dict[str, str]:
    validated = dict(CONFIG)
    for key in ("TESLALOGGER_PORT", "GRAFANA_PORT", "WEBSERVER_PORT"):
        value = candidate.get(key, "").strip()
        if not value.isdigit() or not 1 <= int(value) <= 65535:
            raise ValueError(f"{key} muss eine Portnummer zwischen 1 und 65535 sein.")
        validated[key] = value
    bind_ip = candidate.get("BIND_IP", "").strip()
    ipaddress.ip_address(bind_ip)
    validated["BIND_IP"] = bind_ip
    timezone_name = candidate.get("TZ", "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_+.-]+(?:/[A-Za-z0-9_+.-]+)*", timezone_name):
        raise ValueError("Ungueltige Zeitzone.")
    validated["TZ"] = timezone_name
    scheme = candidate.get("PUBLIC_SCHEME", "http").strip().lower()
    if scheme not in {"http", "https"}:
        raise ValueError("URL-Schema muss http oder https sein.")
    validated["PUBLIC_SCHEME"] = scheme
    host = candidate.get("PUBLIC_HOST", "").strip()
    if host and not re.fullmatch(r"[A-Za-z0-9.-]+(?::[0-9]{1,5})?", host):
        raise ValueError("Domain/IP enthaelt ungueltige Zeichen.")
    validated["PUBLIC_HOST"] = host
    return validated


def write_env(config: dict[str, str]) -> None:
    values = {**config, **SECRETS}
    if validate_architecture() == "linux/arm64":
        values["TESLALOGGER_LD_PRELOAD"] = "/usr/lib/aarch64-linux-gnu/libfreetype.so.6:/usr/lib/aarch64-linux-gnu/libuuid.so.1"
    else:
        values["TESLALOGGER_LD_PRELOAD"] = ""
    lines = [f"{key}={value}" for key, value in sorted(values.items())]
    atomic_write(ENV_FILE, "\n".join(lines) + "\n")


def ensure_volumes() -> None:
    existing = set(docker("volume", "ls", "--format", "{{.Name}}").splitlines())
    for volume in PROTECTED_VOLUMES:
        if volume not in existing:
            docker("volume", "create", "--label", "io.teslalogger.qnap.protected=true", volume)


def existing_container_conflict() -> None:
    for name in ("teslalogger", "teslalogger-db", "teslalogger-grafana", "teslalogger-webserver"):
        inspected = docker("inspect", name, "--format", "{{ index .Config.Labels \"io.teslalogger.qnap.managed\" }}", check=False).strip()
        if inspected and inspected != "true":
            raise RuntimeError(f"Container '{name}' existiert bereits und gehoert nicht diesem Manager. Aus Datenschutzgruenden wurde nichts veraendert.")


def port_available(port: int, owner: str) -> bool:
    users = docker("ps", "--filter", f"publish={port}", "--format", "{{.Names}}", check=False).split()
    if users:
        return all(user == owner for user in users)
    probe = f"teslalogger-qnap-port-check-{port}-{os.getpid()}"
    result = docker(
        "run", "--detach", "--rm", "--name", probe, "--publish", f"{port}:9/tcp",
        ALPINE_IMAGE, "sleep", "10", check=False, timeout=120
    ).strip()
    docker("rm", "--force", probe, check=False)
    return bool(result) and "error" not in result.lower()


def adapt_ports(config: dict[str, str]) -> tuple[dict[str, str], list[str]]:
    adapted = dict(config)
    notices: list[str] = []
    mappings = [
        ("TESLALOGGER_PORT", "teslalogger"),
        ("GRAFANA_PORT", "teslalogger-grafana"),
        ("WEBSERVER_PORT", "teslalogger-webserver"),
    ]
    selected: set[int] = set()
    for key, owner in mappings:
        preferred = int(adapted[key])
        for candidate in range(preferred, min(preferred + 100, 65536)):
            if candidate not in selected and port_available(candidate, owner):
                adapted[key] = str(candidate)
                selected.add(candidate)
                if candidate != preferred:
                    notices.append(f"{key}: {preferred} war belegt, verwende {candidate}.")
                break
        else:
            raise RuntimeError(f"Kein freier Port fuer {key} im Bereich {preferred}-{min(preferred + 99, 65535)}.")
    return adapted, notices


def wait_for_stack(timeout: int = 900) -> str:
    deadline = time.time() + timeout
    required = ["teslalogger-db", "teslalogger-grafana", "teslalogger-webserver", "teslalogger"]
    last = ""
    while time.time() < deadline:
        states = []
        healthy = True
        for name in required:
            raw = docker("inspect", name, "--format", "{{.State.Status}}|{{if .State.Health}}{{.State.Health.Status}}{{end}}", check=False).strip()
            states.append(f"{name}: {raw or 'fehlt'}")
            if not raw.startswith("running|") or raw.endswith("|unhealthy") or raw.endswith("|starting"):
                healthy = False
        last = "\n".join(states)
        if healthy:
            return last
        time.sleep(10)
    raise RuntimeError(f"Healthcheck-Timeout nach {timeout} Sekunden.\n{last}")


def install_or_apply(candidate: dict[str, str]) -> str:
    global CONFIG
    validate_architecture()
    existing_container_conflict()
    ensure_volumes()
    docker("pull", ALPINE_IMAGE, timeout=600)
    adapted, notices = adapt_ports(validate_config(candidate))
    CONFIG = adapted
    save_json(CONFIG_FILE, CONFIG)
    write_env(CONFIG)
    output = compose("pull", "--policy", "missing", timeout=1800)
    output += compose("up", "--detach", "--remove-orphans", timeout=1800)
    output += "\n" + wait_for_stack()
    if notices:
        output += "\n\nPortanpassungen:\n" + "\n".join(notices)
    return output


def backup_stack(reason: str = "manual") -> Path:
    ensure_volumes()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    snapshot = BACKUP_DIR / f"teslalogger-{stamp}-{reason}"
    snapshot.mkdir(mode=0o700)
    shutil.copy2(CONFIG_FILE, snapshot / "config.json")
    shutil.copy2(SECRETS_FILE, snapshot / "secrets.json")
    shutil.copy2(COMPOSE_FILE, snapshot / "compose.yaml")
    if ENV_FILE.exists():
        shutil.copy2(ENV_FILE, snapshot / ".env")

    database_running = docker("inspect", "teslalogger-db", "--format", "{{.State.Running}}", check=False).strip() == "true"
    if database_running:
        dump = run([
            "docker", "exec", "teslalogger-db", "sh", "-c",
            'exec mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" --all-databases --single-transaction --routines --events'
        ], timeout=1200)
        atomic_write(snapshot / "database.sql", dump, 0o600)

    docker("pull", ALPINE_IMAGE, timeout=600)
    archived_volumes = list(ARCHIVE_VOLUMES)
    if not database_running:
        archived_volumes.append("teslalogger_qnap_mysql")
    paused: list[str] = []
    try:
        for container in ("teslalogger", "teslalogger-grafana", "teslalogger-webserver"):
            if docker("inspect", container, "--format", "{{.State.Running}}", check=False).strip() == "true":
                docker("pause", container)
                paused.append(container)
        for volume in archived_volumes:
            docker(
                "run", "--rm", "--volume", f"{volume}:/source:ro",
                "--volume", f"{snapshot}:/backup", ALPINE_IMAGE,
                "tar", "czf", f"/backup/{volume}.tar.gz", "-C", "/source", ".",
                timeout=1200
            )
    finally:
        for container in reversed(paused):
            docker("unpause", container, check=False)
    manifest = {
        "created_utc": stamp,
        "reason": reason,
        "volumes": archived_volumes,
        "database_dump": database_running,
        "architecture": validate_architecture(),
    }
    atomic_write(snapshot / "manifest.json", json.dumps(manifest, indent=2) + "\n")
    archive = BACKUP_DIR / f"{snapshot.name}.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(snapshot, arcname=snapshot.name)
    shutil.rmtree(snapshot)
    archive.chmod(0o600)
    return archive


def restore_backup(archive: Path) -> str:
    global CONFIG, SECRETS
    if archive.parent.resolve() != BACKUP_DIR.resolve() or not archive.name.endswith(".tar.gz"):
        raise ValueError("Ungueltiges Backup.")
    safety = backup_stack("before-restore")
    compose("down", "--remove-orphans", timeout=600, check=False)
    work = DATA_DIR / "restore"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(mode=0o700)
    with tarfile.open(archive, "r:gz") as tar:
        for member in tar.getmembers():
            target = (work / member.name).resolve()
            if work.resolve() not in target.parents and target != work.resolve():
                raise RuntimeError("Unsicherer Pfad im Backup.")
        tar.extractall(work, filter="data")
    snapshot = next(path for path in work.iterdir() if path.is_dir())
    ensure_volumes()
    for volume in ARCHIVE_VOLUMES:
        volume_archive = snapshot / f"{volume}.tar.gz"
        if volume_archive.exists():
            docker(
                "run", "--rm", "--volume", f"{volume}:/target",
                "--volume", f"{snapshot}:/backup:ro", ALPINE_IMAGE, "sh", "-c",
                f"find /target -mindepth 1 -delete && tar xzf /backup/{volume}.tar.gz -C /target",
                timeout=1200
            )
    raw_mysql = snapshot / "teslalogger_qnap_mysql.tar.gz"
    if raw_mysql.exists():
        docker(
            "run", "--rm", "--volume", "teslalogger_qnap_mysql:/target",
            "--volume", f"{snapshot}:/backup:ro", ALPINE_IMAGE, "sh", "-c",
            "find /target -mindepth 1 -delete && tar xzf /backup/teslalogger_qnap_mysql.tar.gz -C /target",
            timeout=1200
        )
    else:
        # Die Datenbank wird aus dem konsistenten SQL-Dump neu aufgebaut. Das
        # unmittelbar davor erzeugte Sicherheitsbackup macht diesen Schritt
        # recoverbar, falls der Restore spaeter fehlschlaegt.
        docker(
            "run", "--rm", "--volume", "teslalogger_qnap_mysql:/target",
            ALPINE_IMAGE, "sh", "-c", "find /target -mindepth 1 -delete",
            timeout=600
        )
    for filename, destination in (("config.json", CONFIG_FILE), ("secrets.json", SECRETS_FILE), ("compose.yaml", COMPOSE_FILE)):
        source = snapshot / filename
        if source.exists():
            shutil.copy2(source, destination)
            destination.chmod(0o600)
    CONFIG = load_json(CONFIG_FILE, DEFAULT_CONFIG)
    SECRETS = load_json(SECRETS_FILE, {})
    write_env(CONFIG)
    compose("up", "--detach", "database", timeout=900)
    deadline = time.time() + 600
    while time.time() < deadline:
        if docker("inspect", "teslalogger-db", "--format", "{{if .State.Health}}{{.State.Health.Status}}{{end}}", check=False).strip() == "healthy":
            break
        time.sleep(10)
    dump_file = snapshot / "database.sql"
    if dump_file.exists() and not raw_mysql.exists():
        run([
            "docker", "exec", "-i", "teslalogger-db", "sh", "-c",
            'exec mysql -uroot -p"$MYSQL_ROOT_PASSWORD"'
        ], stdin=dump_file.read_bytes(), timeout=1200)
    compose("up", "--detach", "--remove-orphans", timeout=1800)
    health = wait_for_stack()
    shutil.rmtree(work, ignore_errors=True)
    return f"Restore erfolgreich. Sicherheitsbackup: {safety.name}\n{health}"


def update_stack() -> str:
    global CONFIG
    backup = backup_stack("before-update")
    rollback_tags: dict[str, str] = {}
    services = {
        "TESLALOGGER_IMAGE": "teslalogger",
        "GRAFANA_IMAGE": "teslalogger-grafana",
        "WEBSERVER_IMAGE": "teslalogger-webserver",
    }
    stamp = int(time.time())
    for key, container in services.items():
        image_id = docker("inspect", container, "--format", "{{.Image}}", check=False).strip()
        if image_id:
            tag = f"teslalogger-qnap-rollback/{container}:{stamp}"
            docker("tag", image_id, tag)
            rollback_tags[key] = tag
    try:
        CONFIG.update({key: DEFAULT_CONFIG[key] for key in services})
        save_json(CONFIG_FILE, CONFIG)
        write_env(CONFIG)
        output = compose("pull", "teslalogger", "grafana", "webserver", timeout=1800)
        output += compose("up", "--detach", "--remove-orphans", timeout=1800)
        output += "\n" + wait_for_stack()
        return f"Backup erstellt: {backup.name}\n\n{output}"
    except Exception as exc:
        if rollback_tags:
            CONFIG.update(rollback_tags)
            save_json(CONFIG_FILE, CONFIG)
            write_env(CONFIG)
            compose("up", "--detach", "--remove-orphans", timeout=1200, check=False)
        raise RuntimeError(f"Update fehlgeschlagen. Backup: {backup.name}. Vorherige Images wurden erneut aktiviert.\n{exc}") from exc


def uninstall(remove_data: bool) -> str:
    if remove_data:
        backup = backup_stack("before-delete-all")
    else:
        backup = None
    output = compose("down", "--remove-orphans", timeout=600, check=False)
    if remove_data:
        for volume in PROTECTED_VOLUMES:
            docker("volume", "rm", volume, check=False)
        output += f"\nDatenvolumes entfernt. Letztes Backup: {backup.name if backup else '-'}"
    else:
        output += "\nContainer entfernt; alle geschuetzten Datenvolumes bleiben erhalten."
    return output


def stack_status() -> str:
    if not ENV_FILE.exists():
        return "Noch nicht eingerichtet."
    return compose("ps", check=False, timeout=30)


def job_worker(title: str, function, *args) -> None:
    try:
        output = str(function(*args))
        ok = True
    except Exception as exc:  # noqa: BLE001 - rendered in local admin interface
        output = f"FEHLER: {exc}"
        ok = False
    with job_lock:
        job_state.update(running=False, title=title, output=output[-100000:], ok=ok)


def start_job(title: str, function, *args) -> None:
    with job_lock:
        if job_state["running"]:
            raise RuntimeError("Es laeuft bereits ein Vorgang.")
        job_state.update(running=True, title=title, output=f"{title} gestartet ...", ok=True)
    threading.Thread(target=job_worker, args=(title, function, *args), daemon=True).start()


def backup_files() -> list[Path]:
    return sorted(BACKUP_DIR.glob("teslalogger-*.tar.gz"), key=lambda path: path.stat().st_mtime, reverse=True)


def is_local_address(value: str) -> bool:
    try:
        address = ipaddress.ip_address(value.split("%", 1)[0])
        return address.is_private or address.is_loopback or address.is_link_local
    except ValueError:
        return False


STYLE = """
body{margin:0;background:#0d151c;color:#e7f1f5;font:16px system-ui,sans-serif}main{max-width:1100px;margin:32px auto;padding:0 18px}
h1{margin-bottom:5px}.lead,.muted{color:#9eb1bc}.card{background:#172631;border:1px solid #2d4655;border-radius:15px;padding:22px;margin:18px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(195px,1fr));gap:14px}label{display:block;color:#b7c9d2;font-size:14px}
input,select{box-sizing:border-box;width:100%;margin-top:6px;padding:10px;border:1px solid #476170;border-radius:8px;background:#0e1b23;color:white}
button,.button{display:inline-block;border:0;border-radius:9px;padding:11px 16px;margin:5px 5px 5px 0;background:#55d6be;color:#092019;font-weight:700;cursor:pointer;text-decoration:none}
.alt{background:#314b5a!important;color:#e7f1f5!important}.danger{background:#d85b68!important;color:white!important}pre{white-space:pre-wrap;overflow:auto;background:#091218;padding:14px;border-radius:9px;max-height:420px}
.warn{border-left:4px solid #ffcc4d;padding-left:12px;color:#ffe8a3}.error{color:#ff8994}.ok{color:#55d6be}code{color:#8ce8d6}.volumes{columns:2}
"""


class Handler(BaseHTTPRequestHandler):
    server_version = "TeslaLoggerQNAPManager/1"

    def local_only(self) -> bool:
        if is_local_address(self.client_address[0]):
            return True
        self.send_error(403, "Manager ist auf lokale Netze beschraenkt")
        return False

    def authorized(self) -> bool:
        header = self.headers.get("Authorization", "")
        try:
            user, password = base64.b64decode(header.removeprefix("Basic ")).decode().split(":", 1)
            return header.startswith("Basic ") and user == "admin" and secrets.compare_digest(password, TOKEN)
        except (ValueError, UnicodeDecodeError):
            return False

    def guard(self) -> bool:
        if not self.local_only():
            return False
        if self.path == "/health":
            return True
        if self.authorized():
            return True
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="TeslaLogger QNAP Manager"')
        self.end_headers()
        return False

    def send_html(self, body: str, status: int = 200) -> None:
        data = body.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self' 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        if not self.guard():
            return
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            return
        if self.path.startswith("/download/"):
            name = self.path.removeprefix("/download/")
            if not re.fullmatch(r"teslalogger-[A-Za-z0-9_-]+\.tar\.gz", name):
                self.send_error(404)
                return
            path = BACKUP_DIR / name
            if not path.is_file():
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/gzip")
            self.send_header("Content-Disposition", f'attachment; filename="{name}"')
            self.send_header("Content-Length", str(path.stat().st_size))
            self.end_headers()
            with path.open("rb") as source:
                shutil.copyfileobj(source, self.wfile)
            return
        self.render_home()

    def render_home(self) -> None:
        with job_lock:
            job = dict(job_state)
        try:
            status = stack_status()
        except Exception as exc:  # noqa: BLE001
            status = f"Statusfehler: {exc}"
        refresh = '<meta http-equiv="refresh" content="5">' if job["running"] else ""
        fields = "".join(
            f'<label>{html.escape(label)}<input name="{key}" value="{html.escape(CONFIG.get(key, ""))}" required></label>'
            for key, label in [
                ("BIND_IP", "Interne Bind-IP"), ("TESLALOGGER_PORT", "TeslaLogger-Port"),
                ("GRAFANA_PORT", "Grafana-Port"), ("WEBSERVER_PORT", "Admin-Port"),
                ("TZ", "Zeitzone"), ("PUBLIC_HOST", "Domain / externe IP (optional)")
            ]
        )
        scheme = CONFIG.get("PUBLIC_SCHEME", "http")
        fields += f'<label>Externes Schema<select name="PUBLIC_SCHEME"><option{" selected" if scheme == "http" else ""}>http</option><option{" selected" if scheme == "https" else ""}>https</option></select></label>'
        backups = backup_files()
        backup_rows = "".join(
            f'<option value="{html.escape(path.name)}">{html.escape(path.name)} ({path.stat().st_size // 1024 // 1024} MiB)</option>' for path in backups
        ) or '<option value="">Keine Backups vorhanden</option>'
        download_links = " ".join(
            f'<a class="button alt" href="/download/{quote(path.name)}">{html.escape(path.name)}</a>' for path in backups[:5]
        ) or "Noch keine Backups."
        public_host = CONFIG.get("PUBLIC_HOST") or "QNAP-IP"
        reverse_target = f"http://{CONFIG.get('BIND_IP') if CONFIG.get('BIND_IP') != '0.0.0.0' else 'QNAP-IP'}:{CONFIG.get('WEBSERVER_PORT')}"
        page = f"""<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">{refresh}<title>TeslaLogger QNAP Manager</title><style>{STYLE}</style></head><body><main>
<h1>TeslaLogger QNAP Manager</h1><p class="lead">Inoffizielles Community-Projekt – Installation, Konfiguration, Updates und Datensicherung.</p>
<div class="card"><h2>Einrichtung &amp; Netzwerk</h2><form method="post"><input type="hidden" name="csrf" value="{html.escape(TOKEN)}"><div class="grid">{fields}</div><p><button name="action" value="apply">Ports pruefen &amp; anwenden</button></p></form>
<p>Admin: <code>{scheme}://{html.escape(public_host)}:{CONFIG.get('WEBSERVER_PORT')}/admin/</code><br>Grafana: <code>{scheme}://{html.escape(public_host)}:{CONFIG.get('GRAFANA_PORT')}</code><br>Reverse-Proxy-Ziel: <code>{html.escape(reverse_target)}</code></p>
<p class="warn">Den Manager-Port niemals ins Internet weiterleiten. Fuer externen Zugriff einen VPN- oder HTTPS-Reverse-Proxy mit eigener Zugriffskontrolle verwenden.</p></div>
<div class="card"><h2>Zugangsdaten</h2><p>Grafana-Benutzer: <code>admin</code><br>Automatisch erzeugtes Grafana-Passwort: <code>{html.escape(SECRETS['GRAFANA_PASSWORD'])}</code></p><p class="muted">Datenbankkennwoerter werden ebenfalls zufaellig erzeugt, aber nicht angezeigt, da sie nur intern von den Containern benoetigt werden.</p></div>
<div class="card"><h2>Betrieb &amp; kontrollierte Updates</h2><form method="post"><input type="hidden" name="csrf" value="{html.escape(TOKEN)}"><button class="alt" name="action" value="start">Start</button><button class="alt" name="action" value="stop">Stop</button><button class="alt" name="action" value="restart">Neustart</button><button name="action" value="update">Backup &amp; Update</button></form><pre>{html.escape(status)}</pre></div>
<div class="card"><h2>Backup &amp; Restore</h2><form method="post"><input type="hidden" name="csrf" value="{html.escape(TOKEN)}"><button name="action" value="backup">Backup erstellen</button><select name="backup">{backup_rows}</select><label>Fuer Restore exakt <code>RESTORE</code> eingeben<input name="confirmation"></label><button class="danger" name="action" value="restore">Ausgewaehltes Backup wiederherstellen</button></form><p>{download_links}</p><p class="muted">Backups liegen zusaetzlich im QNAP-Ordner <code>{html.escape(str(BACKUP_DIR))}</code>.</p></div>
<div class="card"><h2>Geschuetzte Volumes – niemals manuell loeschen</h2><p class="volumes">{'<br>'.join(map(html.escape, PROTECTED_VOLUMES))}<br>teslalogger_qnap_manager_data</p></div>
<div class="card"><h2>Deinstallation</h2><form method="post"><input type="hidden" name="csrf" value="{html.escape(TOKEN)}"><button class="alt" name="action" value="uninstall-keep">Nur Container entfernen, Daten behalten</button><label>Fuer vollstaendige Datenloeschung exakt <code>ALLE DATEN LOESCHEN</code> eingeben<input name="delete_confirmation"></label><button class="danger" name="action" value="uninstall-all">Container und Datenvolumes entfernen</button></form></div>
<div class="card"><h2>Letzter Vorgang</h2><p class="{'ok' if job['ok'] else 'error'}">{html.escape(str(job['title']))}{' – laeuft' if job['running'] else ''}</p><pre>{html.escape(str(job['output']))}</pre></div>
</main></body></html>"""
        self.send_html(page)

    def do_POST(self) -> None:  # noqa: N802
        if not self.guard():
            return
        length = int(self.headers.get("Content-Length", "0"))
        form = {key: values[0] for key, values in parse_qs(self.rfile.read(length).decode()).items()}
        if not secrets.compare_digest(form.get("csrf", ""), TOKEN):
            self.send_error(403)
            return
        action = form.get("action", "")
        try:
            if action == "apply":
                start_job("Konfiguration anwenden", install_or_apply, form)
            elif action == "backup":
                start_job("Backup erstellen", lambda: f"Backup erstellt: {backup_stack().name}")
            elif action == "restore":
                if form.get("confirmation") != "RESTORE":
                    raise ValueError("Restore-Bestaetigung fehlt.")
                start_job("Backup wiederherstellen", restore_backup, BACKUP_DIR / form.get("backup", ""))
            elif action == "update":
                start_job("Backup und Update", update_stack)
            elif action in {"start", "stop", "restart"}:
                if action == "start":
                    start_job("Stack starten", lambda: compose("up", "--detach") + "\n" + wait_for_stack())
                elif action == "stop":
                    start_job("Stack stoppen", compose, "stop")
                else:
                    start_job("Stack neu starten", lambda: compose("restart") + "\n" + wait_for_stack())
            elif action == "uninstall-keep":
                start_job("Container entfernen", uninstall, False)
            elif action == "uninstall-all":
                if form.get("delete_confirmation") != "ALLE DATEN LOESCHEN":
                    raise ValueError("Ausdrueckliche Loeschbestaetigung fehlt.")
                start_job("Backup und vollstaendige Deinstallation", uninstall, True)
            else:
                raise ValueError("Unbekannte Aktion.")
        except Exception as exc:  # noqa: BLE001
            with job_lock:
                job_state.update(running=False, title="Fehler", output=str(exc), ok=False)
        self.send_response(303)
        self.send_header("Location", "/")
        self.end_headers()

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"[manager] {self.client_address[0]} {fmt % args}", flush=True)


print("TeslaLogger QNAP Manager", flush=True)
print(f"Architektur: {validate_architecture()}", flush=True)
print(f"Benutzer: admin\nEinmalig erzeugtes Passwort: {TOKEN}", flush=True)
print("Der Manager akzeptiert ausschliesslich lokale/private Client-Adressen.", flush=True)
ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
