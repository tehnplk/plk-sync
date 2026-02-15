from datetime import datetime
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from psycopg.types.json import Json

from db import get_connection


class RawCreateRequest(BaseModel):
    hoscode: str = Field(min_length=1, max_length=20)
    source: str = Field(min_length=1, max_length=255)
    payload: dict[str, Any]
    sync_datetime: datetime | None = None


app = FastAPI(title="PLK Sync Raw API", version="1.0.0")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/raw")
def create_raw_record(request: RawCreateRequest):
    insert_sql = """
        INSERT INTO raw (hoscode, source, payload, sync_datetime)
        VALUES (%s, %s, %s::jsonb, COALESCE(%s, NOW()))
        RETURNING hoscode, source, payload, sync_datetime;
    """

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    insert_sql,
                    (
                        request.hoscode,
                        request.source,
                        Json(request.payload),
                        request.sync_datetime,
                    ),
                )
                created = cur.fetchone()
            conn.commit()
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Database insert failed: {error}")

    return {
        "message": "inserted",
        "data": {
            "hoscode": created[0],
            "source": created[1],
            "payload": created[2],
            "sync_datetime": created[3],
        },
    }
