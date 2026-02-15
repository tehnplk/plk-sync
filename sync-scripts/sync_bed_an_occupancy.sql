-- hos ส่งข้อมูล --
SELECT
  (SELECT hospitalcode FROM opdconfig LIMIT 1) AS hoscode
 ,'xxxxxx' AS an_censored
 ,a.bedno
 ,b.export_code
 ,i.regdate
 ,i.dchdate
 ,GREATEST(i.regdate, DATE('2025-01-01')) AS calc_start
 ,LEAST(i.dchdate, CURDATE()) AS calc_end
 ,CASE
    WHEN LEAST(i.dchdate, CURDATE()) >= GREATEST(i.regdate, DATE('2025-01-01'))
      THEN DATEDIFF(LEAST(i.dchdate, CURDATE()), GREATEST(i.regdate, DATE('2025-01-01'))) + 1
    ELSE 0
  END AS overlap_days
 ,NOW() AS d_update
FROM ipt i
JOIN iptadm a ON a.an = i.an
JOIN bedno b ON b.bedno = a.bedno
WHERE i.regdate IS NOT NULL
  AND i.dchdate IS NOT NULL
  AND i.regdate <= CURDATE()
  AND i.dchdate >= DATE('2025-01-01')
  AND b.export_code IS NOT NULL
  AND TRIM(b.export_code) <> ''
ORDER BY i.regdate, i.an;