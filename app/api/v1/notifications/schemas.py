from pydantic import BaseModel, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

class NotificationBase(BaseModel):
    title: str
    message: str
    type: str  # e.g., 'payment', 'case_status', 'report'
    is_read: bool = False
    metadata_info: Optional[Dict[str, Any]] = None

class NotificationCreate(NotificationBase):
    user_id: UUID

class NotificationResponse(NotificationBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    link: Optional[str] = None
    
    @model_validator(mode='before')
    @classmethod
    def extract_link(cls, data: Any) -> Any:
        if hasattr(data, 'metadata_info') and data.metadata_info:
            if isinstance(data.metadata_info, dict):
                data.link = data.metadata_info.get('link')
        elif isinstance(data, dict) and data.get('metadata_info'):
            data['link'] = data['metadata_info'].get('link')
        return data
    
    class Config:
        from_attributes = True

class UnreadCountResponse(BaseModel):
    unread_count: int
