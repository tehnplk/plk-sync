SELECT
  (SELECT hospitalcode FROM opdconfig LIMIT 1) AS hoscode
 ,yr
 ,yr + 543 AS yr_be
 ,total_cases
 ,admitted_cases
 ,refer_out_cases
 ,avg_wait_min
 ,ROUND(avg_wait_min / 60.0, 2) AS avg_wait_hours
 ,avg_admit_wait_min
 ,ROUND(avg_admit_wait_min / 60.0, 2) AS avg_admit_wait_hr
 ,avg_refer_wait_min
 ,ROUND(avg_refer_wait_min / 60.0, 2) AS avg_refer_wait_hr
 ,pct_over_4hr
 ,NOW() AS d_update
FROM (
  SELECT
    yr
   ,COUNT(*) AS total_cases
   ,SUM(CASE WHEN disposition = 'Admitted' THEN 1 ELSE 0 END) AS admitted_cases
   ,SUM(CASE WHEN disposition = 'Refer Out' THEN 1 ELSE 0 END) AS refer_out_cases
   ,ROUND(AVG(wait_min), 1) AS avg_wait_min
   ,ROUND(AVG(CASE WHEN disposition='Admitted' THEN wait_min END), 1) AS avg_admit_wait_min
   ,ROUND(AVG(CASE WHEN disposition='Refer Out' THEN wait_min END), 1) AS avg_refer_wait_min
   ,ROUND(SUM(CASE WHEN wait_min > 240 THEN 1 ELSE 0 END)*100.0/COUNT(*), 1) AS pct_over_4hr
  FROM (
    -- Admitted: enter_er_time → ipt.regdate+regtime
    SELECT
      YEAR(er.vstdate) AS yr
     ,'Admitted' AS disposition
     ,TIMESTAMPDIFF(MINUTE, er.enter_er_time, 
        CONCAT(ipt.regdate,' ',ipt.regtime)) AS wait_min
    FROM er_regist er
    INNER JOIN ipt ON er.vn = ipt.vn
    WHERE er.er_emergency_level_id IN (1,2) AND er.er_dch_type = 3
      AND er.enter_er_time IS NOT NULL
      AND ipt.regdate IS NOT NULL AND ipt.regtime IS NOT NULL
      AND TIMESTAMPDIFF(MINUTE, er.enter_er_time, 
        CONCAT(ipt.regdate,' ',ipt.regtime)) BETWEEN 0 AND 1440
      AND YEAR(er.vstdate) >= 2020

    UNION ALL

    -- Refer Out: enter_er_time → referout.refer_date+refer_time
    SELECT
      YEAR(er.vstdate) AS yr
     ,'Refer Out' AS disposition
     ,TIMESTAMPDIFF(MINUTE, er.enter_er_time, 
        CONCAT(ro.refer_date,' ',ro.refer_time)) AS wait_min
    FROM er_regist er
    INNER JOIN referout ro ON er.vn = ro.vn
    WHERE er.er_emergency_level_id IN (1,2) AND er.er_dch_type = 2
      AND er.enter_er_time IS NOT NULL
      AND ro.refer_date IS NOT NULL AND ro.refer_time IS NOT NULL
      AND TIMESTAMPDIFF(MINUTE, er.enter_er_time, 
        CONCAT(ro.refer_date,' ',ro.refer_time)) BETWEEN 0 AND 1440
      AND YEAR(er.vstdate) >= 2020
  ) combined
  GROUP BY yr
) summary
ORDER BY yr DESC;