# FastAPI Raw Ingest Server

## 1) Install dependencies

```bash
pip install -r requirements.txt
```

## 2) Configure environment

Copy `.env.example` to `.env` and update `DATABASE_URL`.

Example:

```env
DATABASE_URL=postgresql://admin:YOUR_PASSWORD@localhost:5432/datacenter
API_HOST=0.0.0.0
API_PORT=8000
```

## 3) Run API

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 4) Test insert

```bash
curl -X POST "http://localhost:8000/raw" \
  -H "Content-Type: application/json" \
  -d "{\"hoscode\":\"10676\",\"payload\":{\"metric\":\"demo\",\"value\":1}}"
```
