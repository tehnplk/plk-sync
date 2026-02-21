import argparse
import json
import os
import re
import sys
import time
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pymysql
import requests
from requests.adapters import HTTPAdapter
from dotenv import load_dotenv
from urllib3.util.retry import Retry

ERROR_LOG_PATH = Path("logs/err_message.log")


def load_config() -> dict[str, Any]:
    load_dotenv()
    return {
        "api_url": os.getenv("API_URL", "http://localhost:8000/raw"),
        "api_batch_url": os.getenv("API_BATCH_URL", ""),
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
        "db_password": os.getenv("HIS_DB_PASSWORD", "112233"),
        "db_name": os.getenv("HIS_DB_NAME", "hos11253"),
        "db_charset": os.getenv("HIS_DB_CHARSET", "utf8mb4"),
        "db_connect_timeout": int(os.getenv("HIS_DB_CONNECT_TIMEOUT", "10")),
        "db_read_timeout": int(os.getenv("HIS_DB_READ_TIMEOUT", "60")),
        "db_write_timeout": int(os.getenv("HIS_DB_WRITE_TIMEOUT", "60")),
        "db_retry_total": int(os.getenv("HIS_DB_RETRY_TOTAL", "2")),
        "db_retry_backoff": float(os.getenv("HIS_DB_RETRY_BACKOFF", "0.5")),
        "sql_base_dir": os.getenv("SQL_BASE_DIR", "sync-scripts"),
    }


def normalize_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    return {key: normalize_value(value) for key, value in row.items()}


def resolve_sync_sql_path(sql_base_dir: str, sync_file: str) -> Path:
    name = sync_file.strip()
    if not name:
        raise ValueError("sync file name is required")

    if not name.endswith(".sql"):
        name = f"{name}.sql"

    if not re.match(r"^\d+_sync_", name):
        raise ValueError("sync file must start with '<number>_sync_'")

    sql_path = Path(sql_base_dir) / name
    if not sql_path.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_path}")

    return sql_path


def read_sql(sql_path: Path) -> str:
    return sql_path.read_text(encoding="utf-8")


def append_error_log(err_message: str) -> None:
    ERROR_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with ERROR_LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(f"{date_time} , {err_message}\n")


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
    return [int(value.strip()) for value in raw_value.split(",") if value.strip().isdigit()]


def build_session(config: dict[str, Any]) -> requests.Session:
    statuses = parse_retry_statuses(config["post_retry_statuses"])
    retry = Retry(
        total=config["post_retry_total"],
        backoff_factor=config["post_retry_backoff"],
        status_forcelist=statuses,
        allowed_methods={"POST"},
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


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
    batch_size = max(1, config["post_batch_size"])
    batch_url = config["api_batch_url"].strip()
    session = build_session(config)
    processed = 0

    def build_body(row_data: dict[str, Any]) -> dict[str, Any]:
        return {
            "hoscode": str(row_data.get("hoscode", "")).strip(),
            "source": sync_file,
            "payload": dict(row_data),
            "sync_datetime": datetime.now(timezone.utc).isoformat(),
        }

    if batch_size > 1 and batch_url:
        batch: list[tuple[int, dict[str, Any]]] = []
        for index, row in enumerate(rows, start=1):
            body = build_body(row)
            if not body["hoscode"]:
                failed += 1
                append_error_log(f"post err: idx={index} missing hoscode")
                print("[SKIP] missing hoscode in row")
                continue
            batch.append((index, body))
            if len(batch) < batch_size:
                continue

            success, failed, processed = post_batch(
                batch_url,
                session,
                batch,
                timeout,
                success,
                failed,
                processed,
                log_every,
            )
            batch = []
            time.sleep(sleep_seconds)

        if batch:
            success, failed, processed = post_batch(
                batch_url,
                session,
                batch,
                timeout,
                success,
                failed,
                processed,
                log_every,
            )
            time.sleep(sleep_seconds)
    else:
        for index, row in enumerate(rows, start=1):
            hoscode = str(row.get("hoscode", "")).strip()
            if not hoscode:
                failed += 1
                append_error_log(f"post err: idx={index} missing hoscode")
                print(f"[SKIP] missing hoscode in row idx={index}")
                continue

            body = build_body(row)

            try:
                response = session.post(api_url, json=body, timeout=timeout)
                if response.status_code < 300:
                    success += 1
                else:
                    failed += 1
                    append_error_log(
                        "post err: idx={idx} hoscode={hoscode} "
                        "status={status} body={body}".format(
                            idx=index,
                            hoscode=hoscode,
                            status=response.status_code,
                            body=response.text,
                        )
                    )
                    print(
                        f"[FAIL] idx={index} hoscode={hoscode} "
                        f"status={response.status_code} body={response.text}"
                    )
            except requests.RequestException as error:
                failed += 1
                append_error_log(f"post err: idx={index} hoscode={hoscode} error={error}")
                print(f"[ERROR] idx={index} hoscode={hoscode} error={error}")
            finally:
                processed += 1
                if log_every and processed % log_every == 0:
                    print(f"Progress: {processed}/{len(rows)} posted")
                time.sleep(sleep_seconds)

    return success, failed


def post_batch(
    batch_url: str,
    session: requests.Session,
    batch: list[tuple[int, dict[str, Any]]],
    timeout: int,
    success: int,
    failed: int,
    processed: int,
    log_every: int,
) -> tuple[int, int, int]:
    bodies = [body for _, body in batch]
    try:
        response = session.post(batch_url, json=bodies, timeout=timeout)
        if response.status_code < 300:
            success += len(bodies)
        else:
            failed += len(bodies)
            append_error_log(
                "post err: batch idx={start}-{end} status={status} body={body}".format(
                    start=batch[0][0],
                    end=batch[-1][0],
                    status=response.status_code,
                    body=response.text,
                )
            )
            print(
                f"[FAIL] batch idx={batch[0][0]}-{batch[-1][0]} "
                f"status={response.status_code} body={response.text}"
            )
    except requests.RequestException as error:
        failed += len(bodies)
        append_error_log(
            f"post err: batch idx={batch[0][0]}-{batch[-1][0]} error={error}"
        )
        print(f"[ERROR] batch idx={batch[0][0]}-{batch[-1][0]} error={error}")

    processed += len(bodies)
    if log_every and processed % log_every == 0:
        print(f"Progress: {processed} rows posted")
    return success, failed, processed


def main() -> int:
    parser = argparse.ArgumentParser(description="Generic sync client for <number>_sync_*.sql")
    parser.add_argument("sync_file", help="sync SQL file name, e.g. 0_sync_test.sql")
    parser.add_argument("--dry-run", action="store_true", help="Print first payload without posting")
    args = parser.parse_args()

    config = load_config()

    sql_path = resolve_sync_sql_path(config["sql_base_dir"], args.sync_file)
    effective_file = sql_path.name
    sql_text = read_sql(sql_path)
    rows = fetch_rows(config, sql_text)

    if not rows:
        print("No data to sync")
        return 0

    print(f"Rows prepared: {len(rows)}")

    if args.dry_run:
        print(json.dumps(rows[0], ensure_ascii=False, indent=2))
        return 0

    success, failed = post_rows(
        config["api_url"],
        config["request_timeout"],
        effective_file,
        rows,
        config,
    )
    print(f"Sync finished ({effective_file}): success={success}, failed={failed}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
