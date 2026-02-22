SELECT xi.xray_items_code, xi.xray_items_name
FROM xray_items xi
WHERE xi.xray_items_name LIKE '%CXR%'
   OR xi.search_keyword LIKE '%CXR%';
