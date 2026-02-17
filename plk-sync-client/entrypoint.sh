#!/bin/sh
set -e

echo "[entrypoint] $(date '+%Y-%m-%d %H:%M:%S') running initial 0_sync_test.sql" >> /app/logs/cron.log
/usr/local/bin/python /app/sync_client.py 0_sync_test.sql >> /app/logs/cron.log 2>&1 || true

echo "[entrypoint] $(date '+%Y-%m-%d %H:%M:%S') starting cron" >> /app/logs/cron.log
exec cron -f
