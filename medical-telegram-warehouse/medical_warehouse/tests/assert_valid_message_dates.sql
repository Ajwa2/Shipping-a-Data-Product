-- Custom test: Ensure message dates are within reasonable range
-- Messages should be from 2020 onwards (reasonable start date for Telegram)
-- and not more than 1 day in the future
-- Test passes if this query returns 0 rows

SELECT 
    message_id,
    message_date,
    channel_name
FROM {{ ref('stg_messages') }}
WHERE message_date IS NOT NULL
  AND (
    message_date < '2020-01-01'::timestamp
    OR message_date > CURRENT_TIMESTAMP + INTERVAL '1 day'
  )
