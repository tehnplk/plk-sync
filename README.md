# PLK Sync Client (Docker)

คู่มือนี้เน้นการใช้งานผ่าน Docker container เป็นหลัก

`sync-client` จะรัน SQL จากไฟล์ `sync_*.sql` แล้วส่งข้อมูลไปที่ API `POST /raw`  
Scheduler ใช้ `cron` ภายใน container

## 0) รันคำสั่งจากโฟลเดอร์ root ของโปรเจกต์

```bash
cd plk-sync
```

> ทุกคำสั่ง Docker ในเอกสารนี้ให้รันจากโฟลเดอร์ root (ที่มีไฟล์ `docker-compose.yml`)

## 1) เตรียมค่า `.env`

คัดลอกไฟล์ตัวอย่างก่อน:

```bash
copy .env.example .env
```

กำหนดค่าในไฟล์ `.env` เช่น

```env
API_URL=http://61.19.112.242:8000/raw
SYNC_SCRIPTS_URL=http://61.19.112.242:8000/sync-scripts
REQUEST_TIMEOUT=15

# การเชื่อมต่อ HIS (Slave)
HIS_DB_HOST=192.168.1.200
HIS_DB_PORT=3306
HIS_DB_USER=root
HIS_DB_PASSWORD=112233
HIS_DB_NAME=hos
HIS_DB_CHARSET=utf8mb4
```

## 2) Start services

```bash
docker compose up -d --build
```

จะได้ 1 container:

- `plk-sync`

## 3) ตรวจสอบสถานะ

```bash
docker ps
docker logs plk-sync
```

## 4) สั่งรัน SQL ด้วยตนเองใน container

```bash
docker exec -it plk-sync python /app/sync_client.py 000_sync_test.sql
```

ตัวอย่างไฟล์อื่น:

```bash
docker exec -it plk-sync python /app/sync_client.py 002_sync_bed_type_all.sql
```

## 5) ตั้งเวลา cron jobs (ใน container)

แก้ไฟล์ `cron.d/sync-client` แล้ว rebuild + restart container

```bash
docker compose down
docker compose up -d --build
```

> หมายเหตุ: ตอนบูท container จะรัน `000_sync_test.sql` 1 ครั้งผ่าน entrypoint ก่อนเริ่ม cron

## 6) Restart ทั้งระบบ

```bash
docker compose down
docker compose up -d --build
```

## 7) ดูไฟล์ log

```bash
dir logs
```
