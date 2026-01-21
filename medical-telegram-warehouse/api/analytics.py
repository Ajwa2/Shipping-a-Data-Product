"""
Analytical API endpoints
Task 4 - Build an Analytical API
"""
from fastapi import APIRouter, HTTPException, Query, Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from typing import List, Optional
import os
from dotenv import load_dotenv

from api import schemas
from api.database import get_db

load_dotenv()

router = APIRouter(
    prefix="/api",
    tags=["analytics"]
)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/medical_warehouse")
engine = create_engine(DATABASE_URL)


@router.get(
    "/reports/top-products",
    response_model=List[schemas.TopProduct],
    summary="Get Top Products",
    description="Returns the most frequently mentioned terms/products across all channels. "
                "Searches message text for common medical product terms and keywords."
)
async def get_top_products(
    limit: int = Query(10, ge=1, le=100, description="Maximum number of products to return")
):
    """
    Get top products/terms mentioned across all channels.
    
    - **limit**: Maximum number of results (1-100)
    - Returns products with mention counts and engagement metrics
    """
    try:
        # Common medical product keywords to search for
        # This is a simplified approach - in production, you might use NLP or a product dictionary
        query = text("""
            WITH product_terms AS (
                SELECT 
                    LOWER(UNNEST(STRING_TO_ARRAY(message_text, ' '))) as term,
                    message_id,
                    channel_key,
                    view_count
                FROM fct_messages
                WHERE message_text IS NOT NULL
                    AND LENGTH(message_text) > 0
            ),
            filtered_terms AS (
                SELECT 
                    term,
                    message_id,
                    channel_key,
                    view_count
                FROM product_terms
                WHERE LENGTH(term) > 3
                    AND term NOT IN ('the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use')
            ),
            term_stats AS (
                SELECT 
                    term,
                    COUNT(DISTINCT message_id) as mention_count,
                    ROUND(AVG(view_count)::NUMERIC, 2) as avg_views,
                    ARRAY_AGG(DISTINCT channel_key) as channel_keys
                FROM filtered_terms
                GROUP BY term
                HAVING COUNT(DISTINCT message_id) >= 2
            )
            SELECT 
                ts.term as product_term,
                ts.mention_count,
                ts.avg_views,
                ARRAY_AGG(DISTINCT dc.channel_name) as channels
            FROM term_stats ts
            LEFT JOIN dim_channels dc ON dc.channel_key = ANY(ts.channel_keys)
            GROUP BY ts.term, ts.mention_count, ts.avg_views
            ORDER BY ts.mention_count DESC, ts.avg_views DESC
            LIMIT :limit
        """)
        
        with engine.connect() as conn:
            result = conn.execute(query, {"limit": limit})
            rows = result.fetchall()
            
            products = []
            for row in rows:
                products.append(schemas.TopProduct(
                    product_term=row[0],
                    mention_count=row[1],
                    avg_views=float(row[2]) if row[2] else 0.0,
                    channels=row[3] if row[3] else []
                ))
            
            return products
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching top products: {str(e)}")


@router.get(
    "/channels/{channel_name}/activity",
    response_model=schemas.ChannelActivity,
    summary="Get Channel Activity",
    description="Returns posting activity and trends for a specific channel. "
                "Includes statistics about posts, engagement, and date ranges."
)
async def get_channel_activity(
    channel_name: str = Path(..., description="Name of the channel to analyze")
):
    """
    Get activity statistics for a specific channel.
    
    - **channel_name**: The channel name (e.g., 'chemed123')
    - Returns comprehensive channel statistics and recent posts
    """
    try:
        # Get channel statistics
        channel_query = text("""
            SELECT 
                channel_key,
                channel_name,
                channel_type,
                total_posts,
                messages_with_media,
                media_ratio,
                avg_views,
                avg_forwards,
                first_post_date,
                last_post_date,
                days_active
            FROM dim_channels
            WHERE LOWER(channel_name) = LOWER(:channel_name)
        """)
        
        # Get recent posts
        recent_posts_query = text("""
            SELECT 
                fm.message_id,
                fm.message_text,
                fm.message_date,
                fm.view_count,
                fm.forward_count,
                fm.has_image
            FROM fct_messages fm
            JOIN dim_channels dc ON fm.channel_key = dc.channel_key
            WHERE LOWER(dc.channel_name) = LOWER(:channel_name)
            ORDER BY fm.message_date DESC
            LIMIT 10
        """)
        
        with engine.connect() as conn:
            # Get channel stats
            result = conn.execute(channel_query, {"channel_name": channel_name})
            channel_row = result.fetchone()
            
            if not channel_row:
                raise HTTPException(
                    status_code=404,
                    detail=f"Channel '{channel_name}' not found"
                )
            
            # Get recent posts
            posts_result = conn.execute(recent_posts_query, {"channel_name": channel_name})
            recent_posts = []
            for post in posts_result:
                recent_posts.append({
                    "message_id": post[0],
                    "message_text": post[1][:100] + "..." if post[1] and len(post[1]) > 100 else (post[1] or ""),
                    "message_date": post[2].isoformat() if post[2] else None,
                    "view_count": post[3],
                    "forward_count": post[4],
                    "has_image": post[5]
                })
            
            return schemas.ChannelActivity(
                channel_name=channel_row[1],
                channel_type=channel_row[2],
                total_posts=channel_row[3],
                messages_with_media=channel_row[4],
                media_ratio=float(channel_row[5]) if channel_row[5] else 0.0,
                avg_views=float(channel_row[6]) if channel_row[6] else 0.0,
                avg_forwards=float(channel_row[7]) if channel_row[7] else 0.0,
                first_post_date=channel_row[8],
                last_post_date=channel_row[9],
                days_active=channel_row[10],
                recent_posts=recent_posts
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching channel activity: {str(e)}")


@router.get(
    "/search/messages",
    response_model=List[schemas.MessageSearchResult],
    summary="Search Messages",
    description="Searches for messages containing a specific keyword. "
                "Searches across message text content and returns matching messages with engagement metrics."
)
async def search_messages(
    query: str = Query(..., min_length=2, description="Search keyword or phrase"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results to return")
):
    """
    Search for messages containing a specific keyword.
    
    - **query**: Search keyword (minimum 2 characters)
    - **limit**: Maximum number of results (1-100)
    - Returns matching messages with full details
    """
    try:
        search_query = text("""
            SELECT 
                fm.message_id,
                dc.channel_name,
                fm.message_text,
                fm.message_date,
                fm.view_count,
                fm.forward_count,
                fm.has_image,
                fid.image_category
            FROM fct_messages fm
            JOIN dim_channels dc ON fm.channel_key = dc.channel_key
            LEFT JOIN fct_image_detections fid ON fm.message_id = fid.message_id
            WHERE LOWER(fm.message_text) LIKE LOWER(:search_pattern)
            ORDER BY fm.view_count DESC, fm.message_date DESC
            LIMIT :limit
        """)
        
        search_pattern = f"%{query}%"
        
        with engine.connect() as conn:
            result = conn.execute(search_query, {
                "search_pattern": search_pattern,
                "limit": limit
            })
            
            messages = []
            for row in result:
                messages.append(schemas.MessageSearchResult(
                    message_id=row[0],
                    channel_name=row[1],
                    message_text=row[2] or "",
                    message_date=row[3],
                    view_count=row[4],
                    forward_count=row[5],
                    has_image=row[6],
                    image_category=row[7]
                ))
            
            return messages
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching messages: {str(e)}")


@router.get(
    "/reports/visual-content",
    response_model=schemas.VisualContentStats,
    summary="Get Visual Content Statistics",
    description="Returns comprehensive statistics about image usage across channels. "
                "Includes YOLO detection results, image categories, and engagement metrics."
)
async def get_visual_content_stats():
    """
    Get visual content statistics across all channels.
    
    Returns:
    - Total images analyzed
    - Distribution by category (promotional, product_display, lifestyle, other)
    - Average objects per image
    - Confidence scores
    - Engagement metrics by category
    - Top detected objects
    - Channel-level statistics
    """
    try:
        # Overall statistics
        overall_query = text("""
            SELECT 
                COUNT(*) as total_images,
                ROUND(AVG(detection_count)::NUMERIC, 2) as avg_objects,
                ROUND(AVG(confidence_score)::NUMERIC, 3) as avg_confidence
            FROM fct_image_detections
        """)
        
        # Category distribution
        category_query = text("""
            SELECT 
                image_category,
                COUNT(*) as count,
                ROUND(COUNT(*)::NUMERIC / SUM(COUNT(*)) OVER () * 100, 1) as percentage
            FROM fct_image_detections
            GROUP BY image_category
            ORDER BY count DESC
        """)
        
        # Engagement by category
        engagement_query = text("""
            SELECT 
                image_category,
                ROUND(AVG(view_count)::NUMERIC, 2) as avg_views,
                ROUND(AVG(forward_count)::NUMERIC, 2) as avg_forwards
            FROM fct_image_detections
            GROUP BY image_category
        """)
        
        # Top detected objects
        objects_query = text("""
            WITH object_list AS (
                SELECT 
                    UNNEST(STRING_TO_ARRAY(detected_objects, ',')) as object_name
                FROM fct_image_detections
                WHERE detected_objects IS NOT NULL
                    AND detected_objects != ''
            )
            SELECT 
                TRIM(object_name) as object_name,
                COUNT(*) as count
            FROM object_list
            WHERE TRIM(object_name) != ''
            GROUP BY TRIM(object_name)
            ORDER BY count DESC
            LIMIT 10
        """)
        
        # Channel statistics
        channel_query = text("""
            SELECT 
                dc.channel_name,
                COUNT(fid.message_id) as images_analyzed,
                ROUND(AVG(fid.detection_count)::NUMERIC, 2) as avg_objects,
                ROUND(AVG(fid.confidence_score)::NUMERIC, 3) as avg_confidence
            FROM fct_image_detections fid
            JOIN dim_channels dc ON fid.channel_key = dc.channel_key
            GROUP BY dc.channel_name
            ORDER BY images_analyzed DESC
        """)
        
        with engine.connect() as conn:
            # Overall stats
            overall_result = conn.execute(overall_query)
            overall_row = overall_result.fetchone()
            total_images = overall_row[0] if overall_row else 0
            avg_objects = float(overall_row[1]) if overall_row and overall_row[1] else 0.0
            avg_confidence = float(overall_row[2]) if overall_row and overall_row[2] else 0.0
            
            # Category distribution
            category_result = conn.execute(category_query)
            images_by_category = {}
            category_percentages = {}
            for row in category_result:
                images_by_category[row[0]] = row[1]
                category_percentages[row[0]] = float(row[2])
            
            # Engagement by category
            engagement_result = conn.execute(engagement_query)
            engagement_by_category = {}
            for row in engagement_result:
                engagement_by_category[row[0]] = {
                    "avg_views": float(row[1]) if row[1] else 0.0,
                    "avg_forwards": float(row[2]) if row[2] else 0.0
                }
            
            # Top detected objects
            objects_result = conn.execute(objects_query)
            top_objects = []
            for row in objects_result:
                top_objects.append({
                    "object_name": row[0],
                    "count": row[1]
                })
            
            # Channel stats
            channel_result = conn.execute(channel_query)
            channel_stats = []
            for row in channel_result:
                channel_stats.append({
                    "channel_name": row[0],
                    "images_analyzed": row[1],
                    "avg_objects": float(row[2]) if row[2] else 0.0,
                    "avg_confidence": float(row[3]) if row[3] else 0.0
                })
            
            return schemas.VisualContentStats(
                total_images_analyzed=total_images,
                images_by_category=images_by_category,
                category_percentages=category_percentages,
                avg_objects_per_image=avg_objects,
                avg_confidence_score=avg_confidence,
                engagement_by_category=engagement_by_category,
                top_detected_objects=top_objects,
                channel_stats=channel_stats
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching visual content stats: {str(e)}")
