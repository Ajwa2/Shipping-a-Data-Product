-- Custom test: Ensure no messages have future dates
-- This test returns rows if any messages have dates in the future (beyond tomorrow)
-- Test passes if this query returns 0 rows

SELECT 
    message_id,
    message_date,
    channel_name
FROM {{ ref('stg_messages') }}
WHERE message_date > CURRENT_TIMESTAMP + INTERVAL '1 day'
  AND message_date IS NOT NULL
