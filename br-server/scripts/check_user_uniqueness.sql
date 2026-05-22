-- Check for duplicate phone numbers across user_types
-- This script helps verify the uniqueness constraint after unifying User and AdminUser models
--
-- Expected result: No rows (empty result set) means no duplicates found
-- If duplicates exist, manual cleanup is needed before the unified model can work correctly

SELECT
    phone,
    COUNT(*) as cnt,
    STRING_AGG(user_type, ', ' ORDER BY user_type) as types
FROM users
WHERE phone IS NOT NULL AND phone != ''
GROUP BY phone
HAVING COUNT(*) > 1;

-- Check for duplicate usernames across user_types
-- Same purpose as phone check, but for username field
--
-- Expected result: No rows (empty result set) means no duplicates found

SELECT
    username,
    COUNT(*) as cnt,
    STRING_AGG(user_type, ', ' ORDER BY user_type) as types
FROM users
WHERE username IS NOT NULL AND username != ''
GROUP BY username
HAVING COUNT(*) > 1;

-- Summary query: count potential issues
SELECT
    'duplicate_phones' as issue_type,
    COUNT(*) as issue_count
FROM (
    SELECT phone
    FROM users
    WHERE phone IS NOT NULL AND phone != ''
    GROUP BY phone
    HAVING COUNT(*) > 1
) t

UNION ALL

SELECT
    'duplicate_usernames' as issue_type,
    COUNT(*) as issue_count
FROM (
    SELECT username
    FROM users
    WHERE username IS NOT NULL AND username != ''
    GROUP BY username
    HAVING COUNT(*) > 1
) t;