---
name: hosxp
description: Use this skill when working with HOSxP Hospital Information System database running on MariaDB container. Trigger this skill when users need to query patient data, population statistics, OPD/IPD records, disease analysis, or generate public health reports from HOSxP database.
license: MIT
---

# HOSxP Database Skill

## Database Connection

| Parameter | Value     |
|-----------|-----------|
| Container | `mariadb` |
| User      | `root`    |
| Password  | `112233`  |
| Database  | `hos11253`|

## Usage

### เชื่อมต่อฐานข้อมูล

ใช้ `docker-mariadb-sql` skill สำหรับการรัน SQL queries:

```bash
docker exec -i mariadb mysql --default-character-set=utf8 -uroot -p112233 hos11253 -e "SELECT ..."
```

### ค้นหาความสัมพันธ์ของตาราง

ใช้ `notebooklm` skill เพื่อวิเคราะห์โครงสร้างและความสัมพันธ์ระหว่างตาราง

## Examples

### ตัวอย่างที่ 1: นับจำนวนประชากรแยกรายหมู่บ้าน

```sql
SELECT 
    v.village_moo AS หมู่ที่,
    v.village_name AS ชื่อหมู่บ้าน,
    COUNT(p.person_id) AS จำนวนประชากร
FROM person p
LEFT JOIN village v ON v.village_id = p.village_id
WHERE p.house_regist_type_id IN (1, 3)
  AND p.person_id IS NOT NULL
GROUP BY v.village_moo, v.village_name
ORDER BY CAST(v.village_moo AS UNSIGNED);
```

### ตัวอย่างที่ 2: นับจำนวนผู้ป่วยโรคทางเดินหายใจ

```sql
SELECT 
    COUNT(DISTINCT o.hn) AS จำนวนผู้ป่วย,
    YEAR(o.vstdate) AS ปี,
    MONTH(o.vstdate) AS เดือน
FROM ovstdiag od
JOIN ovst o ON o.vn = od.vn
WHERE od.icd10 LIKE 'J%'
  AND YEAR(o.vstdate) = 2568
GROUP BY YEAR(o.vstdate), MONTH(o.vstdate)
ORDER BY ปี, เดือน;
```

### ตัวอย่างที่ 3: ดึงข้อมูลผู้ป่วยพร้อมที่อยู่แบบเต็ม

```sql
SELECT 
    p.hn,
    p.cid,
    CONCAT(p.pname, p.fname, ' ', p.lname) AS patient_name,
    p.addrpart AS house_no,
    p.moopart AS moo,
    t3.name AS tambon,
    t2.name AS amphur,
    t1.name AS changwat
FROM patient p
-- ดึงชื่อตำบล (รหัสจังหวัด 2 หลัก + อำเภอ 2 หลัก + ตำบล 2 หลัก)
LEFT JOIN thaiaddress t3 ON t3.addressid = CONCAT(p.chwpart, p.amppart, p.tmbpart)
-- ดึงชื่ออำเภอ (รหัสจังหวัด 2 หลัก + อำเภอ 2 หลัก + '00')
LEFT JOIN thaiaddress t2 ON t2.addressid = CONCAT(p.chwpart, p.amppart, '00')
-- ดึงชื่อจังหวัด (รหัสจังหวัด 2 หลัก + '0000')
LEFT JOIN thaiaddress t1 ON t1.addressid = CONCAT(p.chwpart, '0000')
LIMIT 10;
```

## Best Practices

1. **Character Encoding**: ใช้ `--default-character-set=utf8` เพื่อแสดงผลภาษาไทยได้ถูกต้อง
2. **Performance**: ใช้ `LIMIT` เมื่อทดสอบ query ครั้งแรก
3. **Date Filtering**: ระวังปี พ.ศ. vs ค.ศ. ในฐานข้อมูล HOSxP มักใช้ ค.ศ.
4. **ICD-10 Codes**: โรคทางเดินหายใจเริ่มด้วย 'J', โรคติดเชื้อเริ่มด้วย 'A' หรือ 'B'
5. **Table Relationships**: ใช้ `notebooklm` skill เพื่อทำความเข้าใจโครงสร้างตารางก่อนเขียน query ซับซ้อน

## Common Tables

### กลุ่มตาราง ทะเบียนประชากรและที่อยู่

- `person`: ข้อมูลประชากรเชิงรุก
- `village`: ข้อมูลหมู่บ้าน
- `patient`: ทะเบียนประวัติผู้ป่วยของโรงพยาบาล
- `thaiaddress`: ข้อมูลรหัสที่อยู่ (ตำบล/อำเภอ/จังหวัด)

### กลุ่มตาราง ทะเบียนผู้ป่วยและการรักษาที่ OPD

- `ovst`: ข้อมูลการมารับบริการ OPD
- `opdscreen`: ข้อมูลซักประวัติ วัดสัญญาณชีพ และประเมิน Triage
- `vn_stat`: สรุปข้อมูลการมารับบริการ OPD แต่ละครั้ง
- `ovstdiag`: การวินิจฉัยโรค OPD
- `opitemrece`: รายการค่าใช้จ่าย ยา และเวชภัณฑ์
- `pttype`: Lookup สิทธิการรักษา (ผูกกับ `ovst.pttype` หรือ `vn_stat.pttype`)

### กลุ่มตาราง IPD

- `ipt`: ข้อมูลการเข้ารับการรักษาของผู้ป่วยใน (IPD)
- `iptdiag`: การวินิจฉัยโรค IPD
- `ipt` (ฟิลด์ `rw`, `adjrw`): ค่า RW/AdjRW (ใช้คำนวณ CMI/วิเคราะห์ภาระงาน)
- `ipt` (ฟิลด์ `drg`, `mdc`, `grouper_version`): ผล DRG/MDC และเวอร์ชัน Grouper
- `ipt_drg_result`: ตารางผลประมวลผล DRG (DRG, MDC, RW, AdjRW, error/warn) แยกตาม `an`
- `ipt_bed_stat`: ข้อมูลสถิติการครองเตียงของผู้ป่วย
- `bedno`: ทะเบียนเตียง

### กลุ่มตาราง LAB

- `lab_head`: ข้อมูลใบสั่ง Lab (Header)
- `lab_order`: ข้อมูลรายการ Lab ย่อยและผลตรวจ
- `lab_items`: ข้อมูลรายการ Lab ทั้งหมดของโรงพยาบาล (Master)

### กลุ่มตาราง x-ray

- `xray_head`: ข้อมูลใบสั่ง X-ray (Header)
- `xray_order`: รายการ X-ray และผลอ่าน
- `xray_items`: รหัสมาตรฐานรายการ X-ray

### กลุ่มตาราง ทันตกรรม

- `dtmain`: ข้อมูลการมารับบริการทันตกรรม
- `dttx`: รายการหัตถการทันตกรรม

### กลุ่มตาราง ER

- `er_regist`: ทะเบียนผู้ป่วยอุบัติเหตุและฉุกเฉิน (ER)
- `er_nursing_detail`: ข้อมูลซักประวัติและคัดกรอง ER
- `er_emergency_level`: Lookup ระดับความเร่งด่วน/ระดับคัดกรอง (ใช้ร่วมกับ `er_regist.er_emergency_level_id`)

### กลุ่มตาราง REFER

- `referin`: ข้อมูลรับผู้ป่วยส่งต่อ (Refer In)
- `referout`: ข้อมูลส่งต่อผู้ป่วย (Refer Out)
- `refer_cause`: Lookup สาเหตุการส่งต่อ (เชื่อมกับ `referout.refer_cause`)
- `moph_refer`: ข้อมูลการส่งต่อผ่านระบบ MOPH Refer (ผูกกับ `vn`/`hn` และอ้างถึง `referout_id`)
- `moph_refer_expire_type`: Lookup ประเภทหมดอายุ/สถานะหมดอายุของรายการส่งต่อในระบบ MOPH Refer

### กลุ่มตาราง การนัดหมาย และ follow up

- `oapp`: ข้อมูลการนัดหมายผู้ป่วย
- `clinicmember`: ทะเบียนผู้ป่วยคลินิกโรคเรื้อรังและคลินิกพิเศษ

### กลุ่มตาราง แผนก คลินิก และห้องตรวจ

- `kskdepartment`: ข้อมูลแผนกและห้องตรวจต่างๆ ในโรงพยาบาล
- `clinic`: ข้อมูลคลินิกเฉพาะโรคและคลินิกพิเศษ
- `spclty`: ข้อมูลสาขาความเชี่ยวชาญทางการแพทย์

### กลุ่มตาราง การฉีดวัคซีน

- `person_vaccine_list`: ประวัติการได้รับวัคซีนของประชากรในเขตรับผิดชอบ (เชิงรุก)
- `ovst_vaccine`: ข้อมูลการฉีดวัคซีนที่มารับบริการที่ OPD
- `vaccine`: ข้อมูลชนิดของวัคซีน (Lookup)

### กลุ่มตาราง งานส่งเสริมป้องกัน และ special PP

- `pp_special`: ข้อมูลงานส่งเสริมป้องกัน (PP) / บริการกลุ่มเป้าหมาย (Special PP)
- `pp_special_code`: Lookup รหัสบริการส่งเสริมป้องกัน
- `pp_special_type`: Lookup ประเภทบริการส่งเสริมป้องกัน
- `provis_ppspecial`: ข้อมูลส่งออก/แมปบริการส่งเสริมป้องกันสำหรับงาน Provis

### กลุ่มตาราง การแพทย์แผนไทย

- `cicd10tm`: ข้อมูลบันทึกรหัสวินิจฉัยแผนไทย (ICD10TM) ต่อการรับบริการ
- `ovst_sks_icd10tm`: ข้อมูล ICD10TM ที่ใช้ในการเบิก/ส่งออก (เชื่อมโยงกับ OPD)
- `icd10tm_operation`: Lookup รหัสหัตถการ/บริการแผนไทย (ICD10TM Operation)
- `ttmt_code`: Lookup รหัสยา/ผลิตภัณฑ์สมุนไพรตามมาตรฐาน TMT/TTMT

### กลุ่มตาราง Telemedicine

- `telehealth_list`: ข้อมูลรายการรับบริการ Telehealth/Telemedicine
- `telehealth_type`: Lookup ประเภท Telehealth/Telemedicine
- `prscrpt_tele_template`: Template ใบสั่งยาสำหรับ Telemedicine
- `telemed_image_type`: Lookup ประเภทไฟล์/รูปภาพที่ใช้ใน Telemedicine

### กลุ่มตาราง Lookup พื้นฐาน (รหัสมาตรฐาน)

- `icd101`: รหัสการวินิจฉัยโรคตามมาตรฐาน ICD-10
- `icd9cm1`: รหัสหัตถการทางการแพทย์ตามมาตรฐาน ICD-9-CM
- `drugitems`: รายการยาทั้งหมดของโรงพยาบาล
- `nondrugitems`: รายการเวชภัณฑ์และค่าธรรมเนียมที่มิใช่ยา

## Related Skills

- `docker-mariadb-sql`: สำหรับรัน SQL commands ใน MariaDB container
- `notebooklm`: สำหรับวิเคราะห์โครงสร้างและความสัมพันธ์ของตาราง
