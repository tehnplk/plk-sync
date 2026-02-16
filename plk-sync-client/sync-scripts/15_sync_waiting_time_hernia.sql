-- Waiting Time รายปี: ไส้เลื่อน (Hernia)
SELECT 
  (SELECT hospitalcode FROM opdconfig LIMIT 1) AS hoscode,
  YEAR(oa.vstdate) AS visit_year,
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
  AND DATEDIFF(oa.nextdate, oa.vstdate) >= 0
GROUP BY YEAR(oa.vstdate)
ORDER BY visit_year;
