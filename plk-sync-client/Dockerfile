# ใช้ Python 3.13-slim
FROM python:3.13-slim

# ตั้งค่า Working Directory
WORKDIR /app

# ติดตั้ง System Dependencies (จำเป็นสำหรับ Library บางตัว เช่น psycopg2 หรือ mysqlclient)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
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

# สั่งให้ Container รันค้างไว้เพื่อรอ Ofelia มาเรียกใช้งาน
CMD ["tail", "-f", "/dev/null"]