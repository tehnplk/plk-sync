SELECT
  (SELECT hospitalcode FROM opdconfig LIMIT 1) AS hoscode,
  2025 AS y,
  d.icd10 AS pdx,
  COALESCE(i10.tname, '(ไม่พบชื่อโรค)') AS pdx_name,
  COUNT(*) AS death_count,
  NOW() AS d_update
FROM ipt i
JOIN iptdiag d
  ON d.an = i.an
 AND d.diagtype = '1'
LEFT JOIN icd101 i10
  ON REPLACE(d.icd10, '.', '') = REPLACE(i10.code, '.', '')
WHERE i.dchtype IN ('08','09')
  AND YEAR(i.dchdate) = 2025
  AND i.ward = '05'
GROUP BY d.icd10, i10.tname
ORDER BY death_count DESC
LIMIT 10;