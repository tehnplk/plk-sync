-- Test sync script
-- Returns current datetime and database info for testing

SELECT 
    (SELECT hospitalcode FROM opdconfig LIMIT 1) AS hoscode,
    '1.0.2-20260217' as version,
    NOW() as d_update
    
LIMIT 1;