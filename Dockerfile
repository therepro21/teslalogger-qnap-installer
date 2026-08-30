# SPDX-License-Identifier: MIT
# Copyright (c) 2026 therepro21
FROM docker:29.7.2-cli

RUN apk add --no-cache python3 curl tzdata && addgroup -S manager && adduser -S -G manager manager

WORKDIR /opt/teslalogger-qnap-manager
COPY qnap_manager.py compose.yaml LICENSE NOTICE.md THIRD_PARTY_NOTICES.md ./

ENV MANAGER_PORT=8080 \
    MANAGER_DATA=/manager-data \
    BACKUP_DIR=/backups \
    STACK_NAME=teslalogger-qnap

EXPOSE 8080
VOLUME ["/manager-data", "/backups"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD curl --fail --silent http://127.0.0.1:8080/health || exit 1

ENTRYPOINT ["python3", "/opt/teslalogger-qnap-manager/qnap_manager.py"]

LABEL org.opencontainers.image.source="https://github.com/therepro21/teslalogger-qnap-installer" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.title="TeslaLogger QNAP Manager" \
      org.opencontainers.image.description="Unofficial QNAP setup and lifecycle manager for TeslaLogger"
