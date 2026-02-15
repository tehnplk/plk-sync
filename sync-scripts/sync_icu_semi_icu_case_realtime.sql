SELECT
  (SELECT hospitalcode FROM opdconfig LIMIT 1) AS hoscode
 ,COUNT(ipt.an) AS icu_case
 ,NOW() AS d_update

FROM ipt
LEFT JOIN iptadm ON iptadm.an = ipt.an
LEFT JOIN bedno ON bedno.bedno = iptadm.bedno
WHERE bedno.export_code IS NOT NULL
  AND CHAR_LENGTH(TRIM(bedno.export_code)) = 6
  AND SUBSTRING(TRIM(bedno.export_code), 4, 1) IN ('2', '3')
  AND ipt.dchstts IS NULL