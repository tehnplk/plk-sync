-- อัตราการใช้ห้องผ่าตัดรายปี
SELECT 
  (SELECT hospitalcode FROM opdconfig LIMIT 1) AS hoscode,
  YEAR(enter_date) AS op_year,
  YEAR(enter_date) + 543 AS op_year_be,
  COUNT(*) AS total_cases,
  SUM(TIMESTAMPDIFF(MINUTE, 
    CONCAT(enter_date, ' ', enter_time), 
    CONCAT(leave_date, ' ', leave_time))) AS total_or_minutes,
  ROUND(SUM(TIMESTAMPDIFF(MINUTE, 
    CONCAT(enter_date, ' ', enter_time), 
    CONCAT(leave_date, ' ', leave_time))) / COUNT(*), 1) AS avg_min_per_case,
  ROUND(SUM(TIMESTAMPDIFF(MINUTE, 
    CONCAT(enter_date, ' ', enter_time), 
    CONCAT(leave_date, ' ', leave_time))) / 60.0, 1) AS total_or_hours,
  COUNT(DISTINCT enter_date) AS actual_or_days,
  COUNT(DISTINCT enter_date) * 480 AS avail_min_1room,
  ROUND(SUM(TIMESTAMPDIFF(MINUTE, 
    CONCAT(enter_date, ' ', enter_time), 
    CONCAT(leave_date, ' ', leave_time))) * 100.0 
    / (COUNT(DISTINCT enter_date) * 480), 2) AS util_pct,
  NOW() AS d_update
FROM operation_list
WHERE enter_date IS NOT NULL 
  AND enter_time IS NOT NULL 
  AND leave_date IS NOT NULL 
  AND leave_time IS NOT NULL
  AND TIMESTAMPDIFF(MINUTE, 
    CONCAT(enter_date, ' ', enter_time), 
    CONCAT(leave_date, ' ', leave_time)) > 0
GROUP BY YEAR(enter_date)
ORDER BY op_year DESC;