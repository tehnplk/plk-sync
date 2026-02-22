-- Test sync script
-- Returns current datetime and database info for testing

SELECT 
    (SELECT hospitalcode FROM opdconfig LIMIT 1) AS hoscode,
    '1.0.4-20260222' as version,
    NOW() as d_update
    
LIMIT 1;