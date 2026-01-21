-- Custom test: Ensure all fact table records have valid foreign keys
-- This test returns rows if any fact records reference non-existent dimension keys
-- Test passes if this query returns 0 rows

SELECT 
    fm.message_id,
    fm.channel_key,
    fm.date_key
FROM {{ ref('fct_messages') }} fm
LEFT JOIN {{ ref('dim_channels') }} dc
    ON fm.channel_key = dc.channel_key
LEFT JOIN {{ ref('dim_dates') }} dd
    ON fm.date_key = dd.date_key
WHERE dc.channel_key IS NULL
   OR dd.date_key IS NULL
