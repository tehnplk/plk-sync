# Client: sync_client

สคริปต์นี้รัน SQL จากไฟล์ `sync_*.sql` (ส่งชื่อไฟล์ผ่าน args) กับฐานข้อมูลต้นทาง (MySQL) แล้วส่งแต่ละแถวเข้า FastAPI `POST /raw`.

## Setup

1. ติดตั้ง dependency

```bash
pip install -r requirements.txt
```

2. คัดลอก `.env.example` เป็น `.env` แล้วแก้ค่าให้ตรงระบบ

## Run

```bash
python sync_client.py sync_bed_an_occupancy.sql
```

หรือส่งเฉพาะชื่อ (ไม่ต้องใส่ `.sql`):

```bash
python sync_client.py sync_drgs_sum
```

## Test แบบไม่พึ่ง DB ต้นทาง

```bash
python sync_client.py sync_bed_an_occupancy.sql --mock
```

## Dry run

```bash
python sync_client.py sync_bed_an_occupancy.sql --dry-run
```
