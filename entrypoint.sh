#!/bin/sh
set -eu

printenv | grep -v "^no_proxy=" >> /etc/environment

echo "[$(date '+%Y-%m-%d %H:%M:%S')] [entrypoint] running initial 000_sync_test.sql" >> /app/logs/cron.log
/usr/local/bin/python /app/sync_client.py 000_sync_test.sql >> /app/logs/cron.log 2>&1 || true

echo "[$(date '+%Y-%m-%d %H:%M:%S')] [entrypoint] starting cron" >> /app/logs/cron.log
exec cron -f
