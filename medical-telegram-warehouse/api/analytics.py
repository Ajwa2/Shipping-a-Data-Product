"""
Analytical API endpoints for medical telegram warehouse
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any, Optional
from api.database import get_db

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/top-products")
async def top_products(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get top N most frequently mentioned products/drugs across all channels.
    This is a simple implementation - you may want to enhance with NLP.
    """
    query = text("""
        SELECT 
            message_text,
            COUNT(*) as mention_count,
            COUNT(DISTINCT channel_name) as channel_count
        FROM raw_messages
        WHERE message_text IS NOT NULL 
            AND LENGTH(message_text) > 10
        GROUP BY message_text
        ORDER BY mention_count DESC
        LIMIT :limit
    """)
    
    result = db.execute(query, {"limit": limit})
    return [
        {
            "product": row[0],
            "mention_count": row[1],
            "channels": row[2]
        }
        for row in result
    ]


@router.get("/channel-stats")
async def channel_stats(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """
    Get statistics per channel including media content analysis
    """
    query = text("""
        SELECT 
            channel_name,
            COUNT(*) as total_messages,
            COUNT(CASE WHEN has_media THEN 1 END) as messages_with_media,
            COUNT(CASE WHEN has_media THEN 1 END)::FLOAT / 
                NULLIF(COUNT(*), 0) as media_ratio,
            AVG(views) as avg_views,
            AVG(forwards) as avg_forwards,
            MIN(message_date) as first_message,
            MAX(message_date) as last_message
        FROM raw_messages
        GROUP BY channel_name
        ORDER BY total_messages DESC
    """)
    
    result = db.execute(query)
    return [
        {
            "channel_name": row[0],
            "total_messages": row[1],
            "messages_with_media": row[2],
            "media_ratio": float(row[3]) if row[3] else 0,
            "avg_views": float(row[4]) if row[4] else 0,
            "avg_forwards": float(row[5]) if row[5] else 0,
            "first_message": row[6].isoformat() if row[6] else None,
            "last_message": row[7].isoformat() if row[7] else None,
        }
        for row in result
    ]


@router.get("/product-price-analysis")
async def product_price_analysis(
    product_name: Optional[str] = Query(None, description="Filter by product name"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Analyze price mentions and availability across channels
    """
    if product_name:
        filter_clause = "AND message_text ILIKE :product_name"
        params = {"product_name": f"%{product_name}%"}
    else:
        filter_clause = ""
        params = {}
    
    query = text(f"""
        SELECT 
            channel_name,
            COUNT(*) as total_mentions,
            COUNT(CASE WHEN message_text ILIKE '%price%' 
                      OR message_text ILIKE '%birr%' 
                      OR message_text ILIKE '%etb%' THEN 1 END) as price_mentions,
            AVG(views) as avg_views
        FROM raw_messages
        WHERE message_text IS NOT NULL
            {filter_clause}
        GROUP BY channel_name
        ORDER BY total_mentions DESC
    """)
    
    result = db.execute(query, params)
    
    return {
        "channels": [
            {
                "channel_name": row[0],
                "total_mentions": row[1],
                "price_mentions": row[2],
                "avg_views": float(row[3]) if row[3] else 0
            }
            for row in result
        ]
    }


@router.get("/visual-content-analysis")
async def visual_content_analysis(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Analyze visual content using YOLO detections
    """
    query = text("""
        SELECT 
            em.channel_name,
            COUNT(*) as enriched_messages,
            jsonb_array_elements_text(em.detected_objects) as object_class,
            COUNT(*) as detection_count
        FROM enriched_messages em
        WHERE em.detected_objects IS NOT NULL
        GROUP BY em.channel_name, object_class
        ORDER BY em.channel_name, detection_count DESC
    """)
    
    result = db.execute(query)
    
    # Group by channel
    channel_data = {}
    for row in result:
        channel = row[0]
        if channel not in channel_data:
            channel_data[channel] = {
                "channel_name": channel,
                "enriched_messages": row[1],
                "detections": []
            }
        channel_data[channel]["detections"].append({
            "object_class": row[2],
            "count": row[3]
        })
    
    return {
        "channels": list(channel_data.values()),
        "summary": {
            "total_enriched_messages": sum(
                ch["enriched_messages"] for ch in channel_data.values()
            )
        }
    }


@router.get("/posting-trends")
async def posting_trends(
    period: str = Query("daily", regex="^(daily|weekly)$"),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get daily or weekly trends in posting volume
    """
    if period == "daily":
        date_trunc = "DATE(message_date)"
        group_by = "DATE(message_date)"
    else:  # weekly
        date_trunc = "DATE_TRUNC('week', message_date)"
        group_by = "DATE_TRUNC('week', message_date)"
    
    query = text(f"""
        SELECT 
            {date_trunc} as period,
            channel_name,
            COUNT(*) as message_count,
            COUNT(CASE WHEN has_media THEN 1 END) as media_count
        FROM raw_messages
        WHERE message_date >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY {group_by}, channel_name
        ORDER BY period DESC, message_count DESC
    """)
    
    result = db.execute(query)
    
    return [
        {
            "period": row[0].isoformat() if hasattr(row[0], 'isoformat') else str(row[0]),
            "channel_name": row[1],
            "message_count": row[2],
            "media_count": row[3]
        }
        for row in result
    ]


@router.get("/product-types")
async def product_types(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get distribution of product types (pills, creams, etc.)
    """
    query = text("""
        SELECT 
            CASE 
                WHEN message_text ILIKE '%pill%' OR message_text ILIKE '%tablet%' 
                     OR message_text ILIKE '%capsule%' THEN 'pill'
                WHEN message_text ILIKE '%cream%' OR message_text ILIKE '%ointment%' 
                     OR message_text ILIKE '%gel%' THEN 'cream'
                WHEN message_text ILIKE '%syrup%' OR message_text ILIKE '%liquid%' THEN 'liquid'
                WHEN message_text ILIKE '%injection%' OR message_text ILIKE '%inject%' THEN 'injection'
                ELSE 'other'
            END as product_type,
            COUNT(*) as count,
            COUNT(DISTINCT channel_name) as channel_count
        FROM raw_messages
        WHERE message_text IS NOT NULL
        GROUP BY product_type
        ORDER BY count DESC
    """)
    
    result = db.execute(query)
    
    return {
        "product_types": [
            {
                "type": row[0],
                "count": row[1],
                "channels": row[2]
            }
            for row in result
        ]
    }
