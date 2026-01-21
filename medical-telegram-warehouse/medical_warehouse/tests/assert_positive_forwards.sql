-- Custom test: Ensure forward counts are non-negative
-- This test returns rows if any messages have negative forward counts
-- Test passes if this query returns 0 rows

SELECT 
    message_id,
    forwards,
    channel_name
FROM {{ ref('stg_messages') }}
WHERE forwards < 0
