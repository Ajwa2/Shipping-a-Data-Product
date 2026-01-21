"""
Pydantic models for API request/response validation
Task 4 - Analytical API
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============================================================================
# Response Models
# ============================================================================

class TopProduct(BaseModel):
    """Schema for top product response"""
    product_term: str = Field(..., description="Product or term mentioned")
    mention_count: int = Field(..., description="Number of times mentioned")
    avg_views: float = Field(..., description="Average views for messages mentioning this term")
    channels: List[str] = Field(..., description="Channels where this term appears")
    
    class Config:
        json_schema_extra = {
            "example": {
                "product_term": "paracetamol",
                "mention_count": 15,
                "avg_views": 1250.5,
                "channels": ["chemed123", "tikvahpharma"]
            }
        }


class ChannelActivity(BaseModel):
    """Schema for channel activity response"""
    channel_name: str = Field(..., description="Channel name")
    channel_type: str = Field(..., description="Channel classification")
    total_posts: int = Field(..., description="Total number of posts")
    messages_with_media: int = Field(..., description="Number of messages with media")
    media_ratio: float = Field(..., description="Ratio of messages with media")
    avg_views: float = Field(..., description="Average views per message")
    avg_forwards: float = Field(..., description="Average forwards per message")
    first_post_date: Optional[datetime] = Field(None, description="Date of first post")
    last_post_date: Optional[datetime] = Field(None, description="Date of last post")
    days_active: Optional[int] = Field(None, description="Number of days active")
    recent_posts: List[dict] = Field(default_factory=list, description="Recent posts summary")
    
    class Config:
        json_schema_extra = {
            "example": {
                "channel_name": "chemed123",
                "channel_type": "Other",
                "total_posts": 76,
                "messages_with_media": 72,
                "media_ratio": 0.95,
                "avg_views": 1418.82,
                "avg_forwards": 3.16,
                "first_post_date": "2022-09-05T08:35:59",
                "last_post_date": "2023-02-10T12:23:06",
                "days_active": 158
            }
        }


class MessageSearchResult(BaseModel):
    """Schema for message search result"""
    message_id: int = Field(..., description="Message ID")
    channel_name: str = Field(..., description="Channel name")
    message_text: str = Field(..., description="Message text content")
    message_date: datetime = Field(..., description="Message timestamp")
    view_count: int = Field(..., description="Number of views")
    forward_count: int = Field(..., description="Number of forwards")
    has_image: bool = Field(..., description="Whether message has an image")
    image_category: Optional[str] = Field(None, description="YOLO image category if available")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message_id": 97,
                "channel_name": "chemed123",
                "message_text": "New paracetamol available...",
                "message_date": "2023-02-10T12:23:06",
                "view_count": 1327,
                "forward_count": 1,
                "has_image": True,
                "image_category": "product_display"
            }
        }


class VisualContentStats(BaseModel):
    """Schema for visual content statistics"""
    total_images_analyzed: int = Field(..., description="Total number of images analyzed")
    images_by_category: dict = Field(..., description="Count of images by category")
    category_percentages: dict = Field(..., description="Percentage distribution by category")
    avg_objects_per_image: float = Field(..., description="Average objects detected per image")
    avg_confidence_score: float = Field(..., description="Average confidence score")
    engagement_by_category: dict = Field(..., description="Average views by image category")
    top_detected_objects: List[dict] = Field(..., description="Top detected objects")
    channel_stats: List[dict] = Field(..., description="Visual content stats by channel")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_images_analyzed": 67,
                "images_by_category": {
                    "promotional": 6,
                    "product_display": 12,
                    "lifestyle": 20,
                    "other": 29
                },
                "category_percentages": {
                    "promotional": 9.0,
                    "product_display": 17.9,
                    "lifestyle": 29.9,
                    "other": 43.3
                },
                "avg_objects_per_image": 2.15,
                "avg_confidence_score": 0.45
            }
        }


class ErrorResponse(BaseModel):
    """Schema for error responses"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Channel not found",
                "detail": "The channel 'invalid_channel' does not exist in the database"
            }
        }


# ============================================================================
# Request Models (for future POST endpoints)
# ============================================================================

class MessageBase(BaseModel):
    """Base message schema"""
    content: str
    channel_id: Optional[str] = None
    timestamp: Optional[datetime] = None


class MessageCreate(MessageBase):
    """Schema for creating a message"""
    pass


class MessageResponse(MessageBase):
    """Schema for message response"""
    id: int
    
    class Config:
        from_attributes = True
