{{ config(materialized='table') }}

SELECT
    em.message_id,
    em.channel_name,
    em.message_date,
    em.image_path,
    em.detected_objects,
    em.yolo_detections,
    em.enriched_at,
    rm.message_text,
    rm.views,
    rm.forwards,
    rm.has_media
FROM {{ source('raw', 'enriched_messages') }} em
LEFT JOIN {{ source('raw', 'raw_messages') }} rm
    ON em.message_id = rm.message_id
WHERE em.detected_objects IS NOT NULL
