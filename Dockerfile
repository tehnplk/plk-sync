# ใช้ Python 3.13-slim
FROM python:3.13-slim

# ตั้งค่า Working Directory
WORKDIR /app

# ติดตั้ง System Dependencies (จำเป็นสำหรับ Library บางตัว เช่น psycopg2 หรือ mysqlclient)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    cron \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# ติดตั้ง Python Dependencies
# (แยก Copy requirements ออกมาก่อนเพื่อใช้ Layer Cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# คัดลอกไฟล์โปรแกรมทั้งหมด
COPY . .

# สร้างโฟลเดอร์สำหรับเก็บ Log ภายใน Container
RUN mkdir -p /app/logs

# ติดตั้ง cron job จากไฟล์ภายใน image
COPY cron.d/sync-client /etc/cron.d/sync-client
RUN chmod 0644 /etc/cron.d/sync-client

# entrypoint สำหรับรันงานครั้งแรกก่อนเริ่ม cron
COPY entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r//' /entrypoint.sh && chmod +x /entrypoint.sh

# รัน cron ใน foreground ผ่าน entrypoint
ENTRYPOINT ["/entrypoint.sh"]