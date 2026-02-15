SELECT 
    (SELECT hospitalcode FROM opdconfig LIMIT 1) AS hoscode,
    v.pdx AS icd10,
    i.name AS icd10_name,
    COUNT(*) AS total_refer,
    NOW() AS d_update
FROM referout r
LEFT JOIN vn_stat v ON v.vn = r.vn
LEFT JOIN icd101 i ON i.code = v.pdx
WHERE r.refer_date BETWEEN '2025-01-01' AND '2025-12-31'
and v.pdx is not NULL
GROUP BY v.pdx
ORDER BY total_refer DESC
LIMIT 10;