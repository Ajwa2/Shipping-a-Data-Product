{{ config(materialized='table') }}

WITH channel_stats AS (
    SELECT
        channel_name,
        channel_title,
        COUNT(DISTINCT message_id) as total_posts,
        COUNT(DISTINCT CASE WHEN has_media THEN message_id END) as messages_with_media,
        AVG(views) as avg_views,
        AVG(forwards) as avg_forwards,
        MIN(message_date) as first_post_date,
        MAX(message_date) as last_post_date
    FROM {{ ref('stg_messages') }}
    WHERE channel_name IS NOT NULL
    GROUP BY channel_name, channel_title
)

SELECT
    -- Surrogate key (using channel_name as key, can be enhanced with sequence)
    ROW_NUMBER() OVER (ORDER BY channel_name) as channel_key,
    
    -- Natural key
    channel_name,
    channel_title,
    
    -- Channel type classification
    CASE 
        WHEN channel_name ILIKE '%pharma%' OR channel_name ILIKE '%drug%' 
             OR channel_name ILIKE '%medicine%' THEN 'Pharmaceutical'
        WHEN channel_name ILIKE '%cosmetic%' OR channel_name ILIKE '%beauty%' 
             OR channel_name ILIKE '%skincare%' THEN 'Cosmetics'
        WHEN channel_name ILIKE '%medical%' OR channel_name ILIKE '%health%' 
             OR channel_name ILIKE '%clinic%' THEN 'Medical'
        ELSE 'Other'
    END as channel_type,
    
    -- Statistics
    total_posts,
    messages_with_media,
    CASE 
        WHEN total_posts > 0 THEN messages_with_media::FLOAT / total_posts
        ELSE 0
    END as media_ratio,
    ROUND(avg_views, 2) as avg_views,
    ROUND(avg_forwards, 2) as avg_forwards,
    
    -- Date information
    first_post_date,
    last_post_date,
    EXTRACT(DAY FROM (last_post_date - first_post_date))::INTEGER as days_active
    
FROM channel_stats
ORDER BY channel_name

