{{ config(materialized='table') }}

SELECT DISTINCT
    channel_name as channel_key,
    channel_name,
    channel_title,
    COUNT(DISTINCT message_id) as total_messages,
    COUNT(DISTINCT CASE WHEN has_media THEN message_id END) as messages_with_media,
    COUNT(DISTINCT CASE WHEN has_media THEN message_id END)::FLOAT / 
        NULLIF(COUNT(DISTINCT message_id), 0) as media_ratio,
    AVG(views) as avg_views,
    AVG(forwards) as avg_forwards,
    MIN(message_date) as first_message_date,
    MAX(message_date) as last_message_date
FROM {{ ref('stg_messages') }}
GROUP BY channel_name, channel_title
