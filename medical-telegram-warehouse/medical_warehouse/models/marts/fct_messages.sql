{{ config(materialized='table') }}

SELECT
    -- Primary key
    sm.message_id,
    
    -- Foreign keys to dimension tables
    dc.channel_key,
    dd.date_key,
    
    -- Message content
    sm.message_text,
    sm.message_length,
    sm.has_text,
    
    -- Media information
    sm.has_media,
    sm.has_image,
    sm.image_path,
    
    -- Engagement metrics
    sm.views as view_count,
    sm.forwards as forward_count,
    
    -- Business logic fields
    CASE 
        WHEN sm.message_text ILIKE '%price%' OR sm.message_text ILIKE '%birr%' 
             OR sm.message_text ILIKE '%etb%' OR sm.message_text ILIKE '%cost%' THEN TRUE 
        ELSE FALSE 
    END as mentions_price,
    
    CASE 
        WHEN sm.message_text ILIKE '%pill%' OR sm.message_text ILIKE '%tablet%' 
             OR sm.message_text ILIKE '%capsule%' THEN 'pill'
        WHEN sm.message_text ILIKE '%cream%' OR sm.message_text ILIKE '%ointment%' 
             OR sm.message_text ILIKE '%gel%' OR sm.message_text ILIKE '%lotion%' THEN 'cream'
        WHEN sm.message_text ILIKE '%syrup%' OR sm.message_text ILIKE '%liquid%' 
             OR sm.message_text ILIKE '%solution%' THEN 'liquid'
        WHEN sm.message_text ILIKE '%injection%' OR sm.message_text ILIKE '%inject%' 
             OR sm.message_text ILIKE '%ampoule%' THEN 'injection'
        WHEN sm.message_text ILIKE '%drops%' OR sm.message_text ILIKE '%eye%' THEN 'drops'
        ELSE 'other'
    END as product_type,
    
    -- Time information (for convenience, also in dim_dates)
    sm.message_date,
    EXTRACT(HOUR FROM sm.message_date) as hour_of_day,
    
    -- Metadata
    sm.loaded_at

FROM {{ ref('stg_messages') }} sm
LEFT JOIN {{ ref('dim_channels') }} dc
    ON sm.channel_name = dc.channel_name
LEFT JOIN {{ ref('dim_dates') }} dd
    ON DATE(sm.message_date) = dd.full_date
WHERE 
    -- Only include messages with valid dimensions
    sm.message_date IS NOT NULL
    AND dc.channel_key IS NOT NULL
    AND dd.date_key IS NOT NULL
