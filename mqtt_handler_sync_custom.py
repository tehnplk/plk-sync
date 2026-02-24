from __future__ import annotations

import os
import re
import sys
import time
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

import paho.mqtt.client as mqtt
import pymysql
import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


MQTT_TOPIC = "sync/custom"
ERROR_LOG_PATH = os.path.join("logs", "err_message.log")


def log(msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def load_config() -> dict[str, Any]:
    load_dotenv()
    return {
        "api_url": os.getenv("API_URL", "http://localhost:8000/raw"),
        "api_batch_url": os.getenv("API_BATCH_URL", ""),
        "sync_scripts_url": os.getenv("SYNC_SCRIPTS_URL", "").strip(),
        "request_timeout": int(os.getenv("REQUEST_TIMEOUT", "15")),
        "post_sleep_ms": int(os.getenv("POST_SLEEP_MS", "300")),
        "post_log_every": int(os.getenv("POST_LOG_EVERY", "100")),
        "post_retry_total": int(os.getenv("POST_RETRY_TOTAL", "3")),
        "post_retry_backoff": float(os.getenv("POST_RETRY_BACKOFF", "0.5")),
        "post_retry_statuses": os.getenv("POST_RETRY_STATUSES", "429,500,502,503,504"),
        "post_batch_size": int(os.getenv("POST_BATCH_SIZE", "1")),
        "db_host": os.getenv("HIS_DB_HOST", "127.0.0.1"),
        "db_port": int(os.getenv("HIS_DB_PORT", "3306")),
        "db_user": os.getenv("HIS_DB_USER", "root"),
        "db_password": os.getenv("HIS_DB_PASSWORD", ""),
        "db_name": os.getenv("HIS_DB_NAME", ""),
        "db_charset": os.getenv("HIS_DB_CHARSET", "utf8mb4"),
        "db_connect_timeout": int(os.getenv("HIS_DB_CONNECT_TIMEOUT", "10")),
        "db_read_timeout": int(os.getenv("HIS_DB_READ_TIMEOUT", "60")),
        "db_write_timeout": int(os.getenv("HIS_DB_WRITE_TIMEOUT", "60")),
        "db_retry_total": int(os.getenv("HIS_DB_RETRY_TOTAL", "2")),
        "db_retry_backoff": float(os.getenv("HIS_DB_RETRY_BACKOFF", "0.5")),
        "mqtt_broker_host": os.getenv("MQTT_BROKER_HOST", "localhost"),
        "mqtt_broker_port": int(os.getenv("MQTT_BROKER_PORT", "1883")),
        "mqtt_broker_username": os.getenv("MQTT_BROKER_USERNAME", ""),
        "mqtt_broker_password": os.getenv("MQTT_BROKER_PASSWORD", ""),
    }


def append_error_log(err_message: str) -> None:
    os.makedirs(os.path.dirname(ERROR_LOG_PATH), exist_ok=True)
    date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(ERROR_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"{date_time} , {err_message}\n")


def normalize_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    return {key: normalize_value(value) for key, value in row.items()}


def is_retryable_mysql_error(error: Exception) -> bool:
    if isinstance(error, (pymysql.err.OperationalError, pymysql.err.InterfaceError)):
        code = error.args[0] if error.args else None
        return code in {2006, 2013, 2014, 2055}
    return "Lost connection to MySQL server" in str(error)


def fetch_rows(config: dict[str, Any], sql_text: str) -> list[dict[str, Any]]:
    retries = max(0, config["db_retry_total"])
    backoff = config["db_retry_backoff"]
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        connection = None
        try:
            connection = pymysql.connect(
                host=config["db_host"],
                port=config["db_port"],
                user=config["db_user"],
                password=config["db_password"],
                database=config["db_name"],
                charset=config["db_charset"],
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=config["db_connect_timeout"],
                read_timeout=config["db_read_timeout"],
                write_timeout=config["db_write_timeout"],
            )
            connection.ping(reconnect=True)
            with connection.cursor() as cursor:
                cursor.execute(sql_text)
                rows = cursor.fetchall()
                return [normalize_row(row) for row in rows]
        except Exception as error:
            last_error = error
            append_error_log(f"sql err: attempt={attempt + 1}/{retries + 1} error={error}")
            if not is_retryable_mysql_error(error) or attempt >= retries:
                raise
            time.sleep(backoff * (2**attempt))
        finally:
            if connection is not None:
                connection.close()
    if last_error:
        raise last_error
    return []


def parse_retry_statuses(raw_value: str) -> list[int]:
    return [int(v.strip()) for v in raw_value.split(",") if v.strip().isdigit()]


def build_session(config: dict[str, Any]) -> requests.Session:
    statuses = parse_retry_statuses(config["post_retry_statuses"])
    retry = Retry(
        total=config["post_retry_total"],
        backoff_factor=config["post_retry_backoff"],
        status_forcelist=statuses,
        allowed_methods={"POST", "GET"},
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def fetch_scripts_index(config: dict[str, Any], sync_scripts_url: str) -> dict[str, Any]:
    base = sync_scripts_url.rstrip("/")
    session = build_session(config)
    response = session.get(base, timeout=int(config["request_timeout"]))
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("sync scripts index must be a JSON object")
    return payload


def fetch_sql_from_endpoint(
    config: dict[str, Any],
    sync_scripts_url: str,
    sync_file: str,
) -> tuple[str, str, bool]:
    name = sync_file.strip()
    if not name:
        raise ValueError("sync file name is required")
    if not name.endswith(".sql"):
        name = f"{name}.sql"
    if not re.match(r"^\d+_sync_", name):
        raise ValueError("sync file must start with '<number>_sync_'")

    base = sync_scripts_url.rstrip("/")
    url = f"{base}/{name}"
    session = build_session(config)
    response = session.get(url, timeout=int(config["request_timeout"]))
    if response.status_code == 404:
        payload = fetch_scripts_index(config, sync_scripts_url)
        if name not in payload:
            return name, "", False
        entry = payload.get(name) or {}
        return name, str(entry.get("sql", "")), bool(entry.get("activate", False))

    response.raise_for_status()
    content_type = response.headers.get("content-type", "").lower()
    if "application/json" in content_type:
        payload = response.json()
        if isinstance(payload, dict) and "sql" in payload:
            return name, str(payload.get("sql", "")), bool(payload.get("activate", False))
        elif isinstance(payload, dict) and isinstance(payload.get("data"), dict):
            data = payload.get("data") or {}
            return name, str(data.get("sql", "")), bool(data.get("activate", False))
        else:
            raise ValueError(f"unexpected JSON format from endpoint: {url}")
    return name, response.text, True


def post_rows(
    api_url: str,
    timeout: int,
    sync_file: str,
    rows: list[dict[str, Any]],
    config: dict[str, Any],
) -> tuple[int, int]:
    success = 0
    failed = 0
    sleep_seconds = config["post_sleep_ms"] / 1000
    log_every = max(0, config["post_log_every"])
    session = build_session(config)
    processed = 0

    def build_body(row_data: dict[str, Any]) -> dict[str, Any]:
        return {
            "hoscode": str(row_data.get("hoscode", "")).strip(),
            "source": sync_file,
            "payload": dict(row_data),
            "sync_datetime": datetime.now(timezone.utc).isoformat(),
        }

    for index, row in enumerate(rows, start=1):
        hoscode = str(row.get("hoscode", "")).strip()
        if not hoscode:
            failed += 1
            append_error_log(f"post err: idx={index} missing hoscode")
            log(f"[SKIP] missing hoscode in row idx={index}")
            continue

        body = build_body(row)
        try:
            response = session.post(api_url, json=body, timeout=timeout)
            if response.status_code < 300:
                success += 1
            else:
                failed += 1
                append_error_log(
                    f"post err: idx={index} hoscode={hoscode} "
                    f"status={response.status_code} body={response.text}"
                )
                log(f"[FAIL] idx={index} hoscode={hoscode} status={response.status_code}")
        except requests.RequestException as error:
            failed += 1
            append_error_log(f"post err: idx={index} hoscode={hoscode} error={error}")
            log(f"[ERROR] idx={index} hoscode={hoscode} error={error}")
        finally:
            processed += 1
            if log_every and processed % log_every == 0:
                log(f"progress: {processed}/{len(rows)} posted")
            time.sleep(sleep_seconds)

    return success, failed


def post_sync_custom(config: dict[str, Any]) -> None:
    sync_scripts_url = config["sync_scripts_url"].strip()
    if not sync_scripts_url:
        log("[MQTT] SYNC_SCRIPTS_URL is not set, skipping")
        return

    sql_file = "999_sync_custom.sql"
    try:
        effective_file, sql_text, is_active = fetch_sql_from_endpoint(
            config,
            sync_scripts_url,
            sql_file,
        )
    except Exception as error:
        log(f"[MQTT] failed to fetch {sql_file}: {error}")
        return

    if not sql_text.strip():
        log(f"[MQTT] [{sql_file}] ไม่พบ script นี้บน server")
        return

    if not is_active:
        log(f"[MQTT] [{sql_file}] skip activate=False")
        return

    try:
        rows = fetch_rows(config, sql_text)
    except Exception as error:
        log(f"[MQTT] [{sql_file}] db error: {error}")
        return

    if not rows:
        log(f"[MQTT] [{effective_file}] no data to sync")
        return

    log(f"[MQTT] [{effective_file}] rows prepared: {len(rows)}")
    success, failed = post_rows(
        config["api_url"],
        config["request_timeout"],
        effective_file,
        rows,
        config,
    )
    status = "success" if failed == 0 else "fail"
    log(f"[MQTT] [{effective_file}] {status} success={success} failed={failed}")


def mqtt_listener(config: dict[str, Any]) -> None:
    topic = MQTT_TOPIC

    def on_connect(client: mqtt.Client, userdata: Any, flags: Any, rc: int) -> None:
        if rc == 0:
            log(f"[MQTT] connected to {config['mqtt_broker_host']}:{config['mqtt_broker_port']}")
            client.subscribe(topic)
            log(f"[MQTT] subscribed to topic: {topic}")
        else:
            log(f"[MQTT] connection failed rc={rc}")

    def on_message(client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
        payload = msg.payload.decode(errors="replace")
        log(f"[MQTT] message received topic={msg.topic} payload={payload}")
        post_sync_custom(config)

    def on_disconnect(client: mqtt.Client, userdata: Any, rc: int) -> None:
        log(f"[MQTT] disconnected rc={rc}")

    client = mqtt.Client()
    username = config["mqtt_broker_username"].strip()
    password = config["mqtt_broker_password"].strip()
    if username:
        client.username_pw_set(username, password or None)

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    client.connect(config["mqtt_broker_host"], config["mqtt_broker_port"], keepalive=60)
    log("[MQTT] starting loop (blocking)...")
    client.loop_forever()


if __name__ == "__main__":
    config = load_config()
    sys.exit(mqtt_listener(config))
