SELECT
  (SELECT hospitalcode FROM opdconfig LIMIT 1) AS hoscode,
  m.y,
  m.m,
  (SELECT COUNT(*)
   FROM referout r
   WHERE r.refer_date BETWEEN '2024-10-01' AND CURRENT_DATE
     AND YEAR(r.refer_date) = m.y
     AND MONTH(r.refer_date) = m.m) AS refer_out_count,
  (SELECT COUNT(*)
   FROM moph_refer mr
   JOIN referout r2 ON r2.referout_id = mr.referout_id
   WHERE r2.refer_date BETWEEN '2024-10-01' AND CURRENT_DATE
     AND YEAR(r2.refer_date) = m.y
     AND MONTH(r2.refer_date) = m.m) AS moph_refer_count,
  NOW() AS d_update
FROM (
  SELECT DISTINCT
    YEAR(refer_date) AS y,
    MONTH(refer_date) AS m
  FROM referout
  WHERE refer_date BETWEEN '2024-10-01' AND CURRENT_DATE
) m
ORDER BY m.y, m.m;