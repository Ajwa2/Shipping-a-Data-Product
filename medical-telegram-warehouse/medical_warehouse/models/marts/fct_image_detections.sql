{{ config(materialized='table') }}

/*
Fact table for image detections from YOLO analysis
Joins enriched_messages (YOLO results) with fct_messages to provide
analytical insights about image content and engagement metrics.
*/

WITH enriched_data AS (
    SELECT
        message_id,
        channel_name,
        image_path,
        detection_count,
        image_category,
        confidence_score,
        has_person,
        has_product,
        detected_objects,
        detections_json
    FROM {{ source('raw', 'enriched_messages') }}
    WHERE image_path IS NOT NULL
),

fact_messages AS (
    SELECT
        message_id,
        channel_key,
        date_key,
        view_count,
        forward_count,
        has_image
    FROM {{ ref('fct_messages') }}
)

SELECT
    -- Primary key
    ed.message_id,
    
    -- Foreign keys
    fm.channel_key,
    fm.date_key,
    
    -- Image detection metrics
    ed.detection_count,
    ed.image_category,
    ed.confidence_score,
    ed.has_person,
    ed.has_product,
    ed.detected_objects,
    
    -- Engagement metrics from fact table
    fm.view_count,
    fm.forward_count,
    
    -- Metadata
    ed.image_path,
    ed.detections_json
    
FROM enriched_data ed
INNER JOIN fact_messages fm
    ON ed.message_id = fm.message_id
WHERE fm.has_image = TRUE  -- Only include messages that have images
