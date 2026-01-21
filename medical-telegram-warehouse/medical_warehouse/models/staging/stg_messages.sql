{{ config(materialized='view') }}

WITH raw_data AS (
    SELECT
        message_id,
        channel_name,
        channel_title,
        message_date,
        message_text,
        has_media,
        image_path,
        views,
        forwards,
        loaded_at
    FROM {{ source('raw', 'telegram_messages') }}
)

SELECT
    -- Primary key
    message_id,
    
    -- Channel information
    LOWER(TRIM(channel_name)) as channel_name,
    TRIM(channel_title) as channel_title,
    
    -- Date casting and validation
    CASE 
        WHEN message_date IS NULL THEN NULL
        WHEN message_date::timestamp < '2020-01-01'::timestamp THEN NULL  -- Filter invalid old dates
        WHEN message_date::timestamp > CURRENT_TIMESTAMP + INTERVAL '1 day' THEN NULL  -- Filter future dates
        ELSE message_date::timestamp
    END as message_date,
    
    -- Text content cleaning
    TRIM(COALESCE(message_text, '')) as message_text,
    
    -- Calculated fields
    LENGTH(COALESCE(message_text, '')) as message_length,
    CASE 
        WHEN TRIM(COALESCE(message_text, '')) = '' THEN FALSE
        ELSE TRUE
    END as has_text,
    
    -- Media information
    COALESCE(has_media, FALSE) as has_media,
    CASE 
        WHEN has_media = TRUE AND image_path IS NOT NULL THEN TRUE
        ELSE FALSE
    END as has_image,
    image_path,
    
    -- Engagement metrics (ensure non-negative)
    GREATEST(COALESCE(views, 0), 0) as views,
    GREATEST(COALESCE(forwards, 0), 0) as forwards,
    
    -- Metadata
    loaded_at
    
FROM raw_data
WHERE 
    -- Remove invalid records
    message_id IS NOT NULL
    AND channel_name IS NOT NULL
    AND channel_name != ''
    -- Keep messages from last 5 years (adjust as needed for historical data)
    AND (message_date IS NULL OR message_date::timestamp >= CURRENT_DATE - INTERVAL '5 years')
