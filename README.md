# PLK Sync Client (Docker)

คู่มือนี้เน้นการใช้งานผ่าน Docker container เป็นหลัก

`sync-client` จะรัน SQL จากไฟล์ `sync_*.sql` แล้วส่งข้อมูลไปที่ API `POST /raw`  
`ofelia` ทำหน้าที่ scheduler สำหรับ cron jobs

## 0) เข้าโฟลเดอร์ย่อยก่อน

```bash
cd plk-sync-client
```

> ทุกคำสั่ง Docker ในเอกสารนี้ให้รันจากโฟลเดอร์ `plk-sync-client`

## 1) เตรียมค่า `.env`

กำหนดค่าในไฟล์ `.env` เช่น

```env
API_URL=http://61.19.112.242:8000/raw
REQUEST_TIMEOUT=15

# การเชื่อมต่อ HIS (Hosxp)
HIS_DB_HOST=192.168.1.200
HIS_DB_PORT=3306
HIS_DB_USER=root
HIS_DB_PASSWORD=112233
HIS_DB_NAME=hos
HIS_DB_CHARSET=utf8mb4

SQL_BASE_DIR=/app/sync-scripts
```

## 2) Start services

```bash
docker-compose up -d --build
```

จะได้ 2 containers:

- `sync-client`
- `ofelia`

## 3) ตรวจสอบสถานะ

```bash
docker ps
docker logs sync-client
docker logs ofelia
```

## 4) สั่งรัน SQL ด้วยตนเองใน container

```bash
docker exec -it sync-client python /app/sync_client.py 0_sync_test.sql
```

ตัวอย่างไฟล์อื่น:

```bash
docker exec -it sync-client python /app/sync_client.py 2_sync_bed_type_all.sql
```

## 5) ตั้งเวลา cron jobs (Ofelia)

แก้ไฟล์ `cron_jobs.ini` แล้ว restart ofelia

```bash
docker-compose restart ofelia
```

ตัวอย่าง schedule:

- ทุก 1 นาที: `* * * * *`
- ทุก 30 วินาที: `@every 30s`

## 6) Restart ทั้งระบบ

```bash
docker-compose down
docker-compose up -d --build
```

## 7) ดูไฟล์ log

```bash
dir ofelia_logs
dir logs
```
