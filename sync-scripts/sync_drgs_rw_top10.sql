SELECT
  (SELECT hospitalcode FROM opdconfig LIMIT 1) AS hoscode
 ,YEAR(dchdate) AS y
 ,MONTH(dchdate) AS m
 ,drg AS drgs_code
 ,SUM(adjrw) AS sum_adj_rw
 ,NOW() AS d_update
FROM ipt

WHERE YEAR(dchdate) = 2026
  AND MONTH(dchdate) = 1
GROUP BY YEAR(dchdate), MONTH(dchdate), drg
ORDER BY sum_adj_rw DESC
LIMIT 10;