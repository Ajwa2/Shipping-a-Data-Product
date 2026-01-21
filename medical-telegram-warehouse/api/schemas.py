"""
Pydantic models for API request/response validation
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

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
