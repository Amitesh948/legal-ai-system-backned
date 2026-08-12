from typing import List, Optional
from uuid import UUID
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field

class CitationBase(BaseModel):
    title: str = Field(..., max_length=500, description="Citation title or case name")
    citation_type: str = Field(..., max_length=50, description="Type: judgment, act, section, article")
    act_name: Optional[str] = Field(None, max_length=300)
    section_number: Optional[str] = Field(None, max_length=50)
    judgment_text: Optional[str] = None
    court_name: Optional[str] = Field(None, max_length=200)
    judgment_date: Optional[date] = None
    case_reference: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = None
    keywords: Optional[List[str]] = Field(default_factory=list)
    category: Optional[str] = Field(None, max_length=100)

class CitationCreate(CitationBase):
    pass

class CitationUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    citation_type: Optional[str] = Field(None, max_length=50)
    act_name: Optional[str] = Field(None, max_length=300)
    section_number: Optional[str] = Field(None, max_length=50)
    judgment_text: Optional[str] = None
    court_name: Optional[str] = Field(None, max_length=200)
    judgment_date: Optional[date] = None
    case_reference: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = None
    keywords: Optional[List[str]] = None
    category: Optional[str] = Field(None, max_length=100)

class CitationResponse(CitationBase):
    id: UUID
    added_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
