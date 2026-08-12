from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class ReportResponse(BaseModel):
    id: UUID
    case_id: UUID
    file_name: str
    status: str
    created_at: datetime
    
    # Custom fields we will attach in the router for frontend convenience
    case_number: Optional[str] = None
    
    class Config:
        from_attributes = True
