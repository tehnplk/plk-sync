SELECT
  (SELECT hospitalcode FROM opdconfig LIMIT 1) AS hoscode
 ,YEAR(dchdate) AS y
 ,MONTH(dchdate) AS m
 ,COUNT(*) AS num_pt
 ,SUM(adjrw) AS sum_adjrw
 ,SUM(adjrw) / NULLIF(COUNT(*), 0) AS cmi
 ,NOW() AS d_update
FROM ipt
WHERE dchdate >= '2024-10-01'
GROUP BY YEAR(dchdate), MONTH(dchdate)
ORDER BY y, m;