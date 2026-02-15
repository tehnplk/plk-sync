-- Test sync script
-- Returns current datetime and database info for testing

SELECT 
    (SELECT hospitalcode FROM opdconfig LIMIT 1) AS hoscode,
    'test' as test_data,
    NOW() as test_datetime
    
LIMIT 1;