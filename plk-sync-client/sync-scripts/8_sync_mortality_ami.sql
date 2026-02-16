-- Mortality รายปี: AMI
SELECT 
  (SELECT hospitalcode FROM opdconfig LIMIT 1) AS hoscode,
  YEAR(i.dchdate) AS discharge_year,
  COUNT(DISTINCT i.an) AS total_admissions,
  COUNT(DISTINCT CASE WHEN i.dchstts = '09' THEN i.an END) AS deaths,
  ROUND(
    COUNT(DISTINCT CASE WHEN i.dchstts = '09' THEN i.an END) * 100.0 
    / NULLIF(COUNT(DISTINCT i.an), 0), 2
  ) AS mortality_rate_pct,
  NOW() AS d_update
FROM ipt i
INNER JOIN iptdiag d ON d.an = i.an
WHERE (d.icd10 LIKE 'I21%' OR d.icd10 LIKE 'I22%')
  AND i.dchdate IS NOT NULL
GROUP BY YEAR(i.dchdate)
ORDER BY discharge_year;
