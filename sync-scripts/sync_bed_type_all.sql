SELECT 
(SELECT hospitalcode FROM opdconfig LIMIT 1) AS hoscode
,b.export_code
,b.bedno
,b.bedtype
,b.roomno
,NOW() AS d_update
FROM bedno b
WHERE b.export_code IS NOT NULL
  AND TRIM(b.export_code) <> ''
  AND CHAR_LENGTH(TRIM(b.export_code)) = 6;