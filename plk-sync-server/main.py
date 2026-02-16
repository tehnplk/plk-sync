from datetime import datetime
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from psycopg.types.json import Json

from config import settings
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

@app.get("/check_last")
def check_last_record():
    select_sql = """
        SELECT hoscode, source, payload, sync_datetime, transform_datetime
        FROM raw 
        ORDER BY sync_datetime DESC 
        LIMIT 1;
    """
    
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(select_sql)
                result = cur.fetchone()
                
        if not result:
            return {"message": "No records found", "data": None}
            
        return {
            "message": "Last record found",
            "data": {
                "hoscode": result[0],
                "source": result[1],
                "payload": result[2],
                "sync_datetime": result[3],
                "transform_datetime": result[4],
            }
        }
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Database query failed: {error}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
