{{ config(materialized='view') }}

SELECT
    message_id,
    channel_name,
    channel_title,
    message_date::timestamp as message_date,
    message_text,
    has_media,
    image_path,
    views,
    forwards,
    loaded_at
FROM {{ source('raw', 'raw_messages') }}
WHERE message_date >= CURRENT_DATE - INTERVAL '30 days'
