{{ config(materialized='table') }}

SELECT
    message_id,
    channel_name,
    message_date,
    DATE(message_date) as message_date_only,
    EXTRACT(DOW FROM message_date) as day_of_week,
    EXTRACT(HOUR FROM message_date) as hour_of_day,
    message_text,
    LENGTH(message_text) as message_length,
    has_media,
    image_path,
    views,
    forwards,
    CASE 
        WHEN message_text ILIKE '%price%' OR message_text ILIKE '%birr%' 
             OR message_text ILIKE '%etb%' THEN TRUE 
        ELSE FALSE 
    END as mentions_price,
    CASE 
        WHEN message_text ILIKE '%pill%' OR message_text ILIKE '%tablet%' 
             OR message_text ILIKE '%capsule%' THEN 'pill'
        WHEN message_text ILIKE '%cream%' OR message_text ILIKE '%ointment%' 
             OR message_text ILIKE '%gel%' THEN 'cream'
        WHEN message_text ILIKE '%syrup%' OR message_text ILIKE '%liquid%' THEN 'liquid'
        WHEN message_text ILIKE '%injection%' OR message_text ILIKE '%inject%' THEN 'injection'
        ELSE 'other'
    END as product_type,
    loaded_at
FROM {{ ref('stg_messages') }}
