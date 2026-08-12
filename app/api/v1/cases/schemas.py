"""
Legal AI System - Case Schemas
================================
Pydantic models for Case management.
"""

from typing import Optional, List
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

class CaseDocumentResponse(BaseModel):
    id: str
    file_name: str
    file_type: str
    file_size: int
    created_at: datetime

    class Config:
        from_attributes = True

class CaseCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    priority: str = Field(default="medium", description="low, medium, high, urgent")

class CaseResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    status: str
    priority: str
    client_id: str
    created_at: datetime
    documents: List[CaseDocumentResponse] = []

    class Config:
        from_attributes = True

class LegalOpinionRequest(BaseModel):
    legal_opinion: str
    winning_probability: int = Field(ge=0, le=100)
    risk_assessment: str
    recommended_actions: str
    ai_summary_edited: Optional[str] = None
    status: str = Field(default="draft", description="draft or finalized")

class LegalOpinionResponse(BaseModel):
    id: str
    case_id: str
    advocate_id: str
    legal_opinion: str
    winning_probability: int
    risk_assessment: str
    recommended_actions: str
    ai_summary_edited: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CaseMessageRequest(BaseModel):
    message_text: str = Field(..., min_length=1)

class CaseMessageResponse(BaseModel):
    id: UUID
    case_id: UUID
    sender_id: UUID
    message_text: str
    is_read: bool
    created_at: datetime
    sender_name: Optional[str] = None # Will populate this in the API
    sender_role: Optional[str] = None

    class Config:
        from_attributes = True
