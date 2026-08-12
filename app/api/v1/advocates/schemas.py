"""
Legal AI System - Advocate Schemas
====================================
Pydantic models for Advocate onboarding and management.
"""

from typing import Optional, List
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProfessionalDetailsUpdate(BaseModel):
    state: str = Field(..., min_length=2)
    district: str = Field(..., min_length=2)
    bar_association: str = Field(..., min_length=2)
    practice_areas: str = Field(..., min_length=2)


class LegalEducationUpdate(BaseModel):
    llb_degree: str = Field(..., min_length=2)
    university: str = Field(..., min_length=2)
    college: str = Field(..., min_length=2)
    graduation_year: int = Field(..., ge=1950, le=datetime.now().year)


class BarCouncilDetailsUpdate(BaseModel):
    state_bar_council: str = Field(..., min_length=2)
    bar_council_id: str = Field(..., min_length=2)
    enrollment_date: str = Field(..., min_length=2)


class VerificationStatusUpdate(BaseModel):
    verification_status: str = Field(..., description="pending, approved, or rejected")


class AdvocateProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    
    # Professional Details
    state: Optional[str]
    district: Optional[str]
    bar_association: Optional[str]
    practice_areas: Optional[str]
    
    # Legal Education
    llb_degree: Optional[str]
    university: Optional[str]
    college: Optional[str]
    graduation_year: Optional[int]
    degree_certificate_path: Optional[str]
    
    # Bar Council
    state_bar_council: Optional[str]
    bar_council_id: Optional[str]
    enrollment_date: Optional[str]
    enrollment_certificate_path: Optional[str]
    aibe_status: Optional[str]
    certificate_of_practice_path: Optional[str]
    
    # Identity
    pan_number: Optional[str]
    pan_document_path: Optional[str]
    gov_id_path: Optional[str]
    photograph_path: Optional[str]
    
    # Status
    verification_status: str
    is_available: bool

    class Config:
        from_attributes = True
