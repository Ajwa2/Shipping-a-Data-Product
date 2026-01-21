-- Custom test: Ensure view counts are non-negative
-- This test returns rows if any messages have negative view counts
-- Test passes if this query returns 0 rows

SELECT 
    message_id,
    views,
    channel_name
FROM {{ ref('stg_messages') }}
WHERE views < 0
