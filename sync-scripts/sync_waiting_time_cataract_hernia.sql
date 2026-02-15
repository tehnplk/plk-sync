-- ============================================================
-- ระยะเวลารอคอยผ่าตัดในกลุ่มโรคเป้าหมาย
-- ต้อกระจก (Cataract) และ ไส้เลื่อน (Hernia)
-- ============================================================
-- เกณฑ์:
--   ต้อกระจก ICD-10 : H25% (Age-related cataract), H26% (Other cataract)
--   ไส้เลื่อน ICD-10 : K40% (Inguinal hernia), K41% (Femoral hernia),
--                       K42% (Umbilical hernia), K43% (Ventral hernia)
--   ระยะเวลารอคอย   : DATEDIFF(nextdate, vstdate) จากตาราง oapp
--   ตาราง            : oapp (นัดหมาย) JOIN ovstdiag (วินิจฉัย OPD)
-- ============================================================

-- 1. ภาพรวมรวมทุกปี - ต้อกระจก (Cataract)
SELECT 
  (SELECT hospitalcode FROM opdconfig LIMIT 1) AS hoscode,
  'ต้อกระจก (Cataract)' AS disease_group,
  COUNT(*) AS total_appointments,
  ROUND(AVG(DATEDIFF(oa.nextdate, oa.vstdate)), 2) AS avg_wait_days,
  MIN(DATEDIFF(oa.nextdate, oa.vstdate)) AS min_wait_days,
  MAX(DATEDIFF(oa.nextdate, oa.vstdate)) AS max_wait_days,
  ROUND(AVG(DATEDIFF(oa.nextdate, oa.vstdate)) / 7, 1) AS avg_wait_weeks,
  NOW() AS d_update
FROM oapp oa
INNER JOIN ovstdiag od ON od.vn = oa.vn
WHERE (od.icd10 LIKE 'H25%' OR od.icd10 LIKE 'H26%')
  AND oa.nextdate IS NOT NULL
  AND oa.vstdate IS NOT NULL
  AND DATEDIFF(oa.nextdate, oa.vstdate) >= 0;

-- 2. ภาพรวมรวมทุกปี - ไส้เลื่อน (Hernia)
SELECT 
  (SELECT hospitalcode FROM opdconfig LIMIT 1) AS hoscode,
  'ไส้เลื่อน (Hernia)' AS disease_group,
  COUNT(*) AS total_appointments,
  ROUND(AVG(DATEDIFF(oa.nextdate, oa.vstdate)), 2) AS avg_wait_days,
  MIN(DATEDIFF(oa.nextdate, oa.vstdate)) AS min_wait_days,
  MAX(DATEDIFF(oa.nextdate, oa.vstdate)) AS max_wait_days,
  ROUND(AVG(DATEDIFF(oa.nextdate, oa.vstdate)) / 7, 1) AS avg_wait_weeks,
  NOW() AS d_update
FROM oapp oa
INNER JOIN ovstdiag od ON od.vn = oa.vn
WHERE (od.icd10 LIKE 'K40%' OR od.icd10 LIKE 'K41%' 
       OR od.icd10 LIKE 'K42%' OR od.icd10 LIKE 'K43%')
  AND oa.nextdate IS NOT NULL
  AND oa.vstdate IS NOT NULL
  AND DATEDIFF(oa.nextdate, oa.vstdate) >= 0;

-- 3. แยกรายปี (ต้อกระจก + ไส้เลื่อน รวมในคิวรี่เดียว)
SELECT 
  YEAR(oa.vstdate) AS visit_year,
  -- ต้อกระจก
  SUM(CASE WHEN od.icd10 LIKE 'H25%' OR od.icd10 LIKE 'H26%' 
      THEN 1 ELSE 0 END) AS cataract_appointments,
  ROUND(AVG(CASE WHEN od.icd10 LIKE 'H25%' OR od.icd10 LIKE 'H26%' 
        THEN DATEDIFF(oa.nextdate, oa.vstdate) END), 2) AS cataract_avg_wait_days,
  ROUND(AVG(CASE WHEN od.icd10 LIKE 'H25%' OR od.icd10 LIKE 'H26%' 
        THEN DATEDIFF(oa.nextdate, oa.vstdate) END) / 7, 1) AS cataract_avg_wait_weeks,
  -- ไส้เลื่อน
  SUM(CASE WHEN od.icd10 LIKE 'K40%' OR od.icd10 LIKE 'K41%' 
           OR od.icd10 LIKE 'K42%' OR od.icd10 LIKE 'K43%' 
      THEN 1 ELSE 0 END) AS hernia_appointments,
  ROUND(AVG(CASE WHEN od.icd10 LIKE 'K40%' OR od.icd10 LIKE 'K41%' 
                  OR od.icd10 LIKE 'K42%' OR od.icd10 LIKE 'K43%' 
        THEN DATEDIFF(oa.nextdate, oa.vstdate) END), 2) AS hernia_avg_wait_days,
  ROUND(AVG(CASE WHEN od.icd10 LIKE 'K40%' OR od.icd10 LIKE 'K41%' 
                  OR od.icd10 LIKE 'K42%' OR od.icd10 LIKE 'K43%' 
        THEN DATEDIFF(oa.nextdate, oa.vstdate) END) / 7, 1) AS hernia_avg_wait_weeks,
  NOW() AS d_update
FROM oapp oa
INNER JOIN ovstdiag od ON od.vn = oa.vn
WHERE (od.icd10 LIKE 'H25%' OR od.icd10 LIKE 'H26%' 
       OR od.icd10 LIKE 'K40%' OR od.icd10 LIKE 'K41%' 
       OR od.icd10 LIKE 'K42%' OR od.icd10 LIKE 'K43%')
  AND oa.nextdate IS NOT NULL 
  AND oa.vstdate IS NOT NULL
  AND DATEDIFF(oa.nextdate, oa.vstdate) >= 0
GROUP BY YEAR(oa.vstdate)
ORDER BY visit_year;
