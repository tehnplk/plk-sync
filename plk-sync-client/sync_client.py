import argparse
import json
import os
import re
import sys
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pymysql
import requests
from dotenv import load_dotenv


def load_config() -> dict[str, Any]:
    load_dotenv()
    return {
        "api_url": os.getenv("API_URL", "http://localhost:8000/raw"),
        "request_timeout": int(os.getenv("REQUEST_TIMEOUT", "15")),
        "db_host": os.getenv("HIS_DB_HOST", "127.0.0.1"),
        "db_port": int(os.getenv("HIS_DB_PORT", "3306")),
        "db_user": os.getenv("HIS_DB_USER", "root"),
        "db_password": os.getenv("HIS_DB_PASSWORD", "112233"),
        "db_name": os.getenv("HIS_DB_NAME", "hos11253"),
        "db_charset": os.getenv("HIS_DB_CHARSET", "utf8mb4"),
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


def fetch_rows(config: dict[str, Any], sql_text: str) -> list[dict[str, Any]]:
    connection = pymysql.connect(
        host=config["db_host"],
        port=config["db_port"],
        user=config["db_user"],
        password=config["db_password"],
        database=config["db_name"],
        charset=config["db_charset"],
        cursorclass=pymysql.cursors.DictCursor,
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql_text)
            rows = cursor.fetchall()
            return [normalize_row(row) for row in rows]
    finally:
        connection.close()


def post_rows(api_url: str, timeout: int, sync_file: str, rows: list[dict[str, Any]]) -> tuple[int, int]:
    success = 0
    failed = 0

    for row in rows:
        hoscode = str(row.get("hoscode", "")).strip()
        if not hoscode:
            failed += 1
            print("[SKIP] missing hoscode in row")
            continue

        sync_datetime_value = datetime.now(timezone.utc).isoformat()

        payload = dict(row)

        body = {
            "hoscode": hoscode,
            "source": sync_file,
            "payload": payload,
            "sync_datetime": sync_datetime_value,
        }

        try:
            response = requests.post(api_url, json=body, timeout=timeout)
            if response.status_code < 300:
                success += 1
            else:
                failed += 1
                print(f"[FAIL] hoscode={hoscode} status={response.status_code} body={response.text}")
        except requests.RequestException as error:
            failed += 1
            print(f"[ERROR] hoscode={hoscode} error={error}")

    return success, failed


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

    success, failed = post_rows(config["api_url"], config["request_timeout"], effective_file, rows)
    print(f"Sync finished ({effective_file}): success={success}, failed={failed}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
