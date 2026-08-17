"""
Legal AI System - Advocate Router
====================================
Endpoints for Advocate onboarding and management.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import os

from app.database.session import get_db
from app.core.security import get_current_user_token
from app.models.advocate import Advocate
from app.api.v1.advocates.schemas import (
    ProfessionalDetailsUpdate,
    LegalEducationUpdate,
    BarCouncilDetailsUpdate,
    AdvocateProfileResponse,
    VerificationStatusUpdate
)
from app.api.common.responses import success_response


router = APIRouter(prefix="/advocates", tags=["advocates"])


@router.get("/me", response_model=dict)
async def get_my_advocate_profile(
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(get_current_user_token)
):
    """Get the current advocate's profile."""
    if token_data.get("role") != "advocate":
        raise HTTPException(status_code=403, detail="Not an advocate")
        
    user_id = token_data.get("sub")
    query = select(Advocate).where(Advocate.user_id == user_id)
    result = await db.execute(query)
    advocate = result.scalars().first()
    
    if not advocate:
        # Create a blank profile if it doesn't exist
        advocate = Advocate(user_id=user_id)
        db.add(advocate)
        await db.commit()
        await db.refresh(advocate)
        
    resp = AdvocateProfileResponse.model_validate(advocate)
    return success_response(message="Profile retrieved", data=resp.model_dump(mode='json'))


@router.post("/onboarding/professional", response_model=dict)
async def update_professional_details(
    data: ProfessionalDetailsUpdate,
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(get_current_user_token)
):
    """Step 1: Professional Details"""
    user_id = token_data.get("sub")
    query = select(Advocate).where(Advocate.user_id == user_id)
    result = await db.execute(query)
    advocate = result.scalars().first()
    
    if not advocate:
        raise HTTPException(status_code=404, detail="Profile not found")
        
    advocate.state = data.state
    advocate.district = data.district
    advocate.bar_association = data.bar_association
    advocate.practice_areas = data.practice_areas
    
    await db.commit()
    return success_response(message="Professional details updated successfully")


@router.post("/onboarding/education", response_model=dict)
async def update_education_details(
    data: LegalEducationUpdate,
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(get_current_user_token)
):
    """Step 2: Legal Education"""
    user_id = token_data.get("sub")
    query = select(Advocate).where(Advocate.user_id == user_id)
    result = await db.execute(query)
    advocate = result.scalars().first()
    
    if not advocate:
        raise HTTPException(status_code=404, detail="Profile not found")
        
    advocate.llb_degree = data.llb_degree
    advocate.university = data.university
    advocate.college = data.college
    advocate.graduation_year = data.graduation_year
    
    await db.commit()
    return success_response(message="Education details updated successfully")


@router.post("/onboarding/bar-council", response_model=dict)
async def update_bar_council_details(
    data: BarCouncilDetailsUpdate,
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(get_current_user_token)
):
    """Step 3: Bar Council"""
    user_id = token_data.get("sub")
    query = select(Advocate).where(Advocate.user_id == user_id)
    result = await db.execute(query)
    advocate = result.scalars().first()
    
    if not advocate:
        raise HTTPException(status_code=404, detail="Profile not found")
        
    advocate.state_bar_council = data.state_bar_council
    advocate.bar_council_id = data.bar_council_id
    advocate.enrollment_date = data.enrollment_date
    
    await db.commit()
    return success_response(message="Bar council details updated successfully")


@router.post("/onboarding/documents", response_model=dict)
async def upload_verification_documents(
    enrollment_certificate: Optional[UploadFile] = File(None),
    pan_document: Optional[UploadFile] = File(None),
    gov_id: Optional[UploadFile] = File(None),
    degree_certificate: Optional[UploadFile] = File(None),
    certificate_of_practice: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(get_current_user_token)
):
    """Upload verification documents for advocate profile."""
    from app.config import get_settings
    from uuid import uuid4
    import os
    
    settings = get_settings()
    user_id = token_data.get("sub")
    query = select(Advocate).where(Advocate.user_id == user_id)
    result = await db.execute(query)
    advocate = result.scalars().first()
    
    if not advocate:
        raise HTTPException(status_code=404, detail="Profile not found")
        
    os.makedirs(settings.upload_dir, exist_ok=True)
    
    async def save_file(file: UploadFile, prefix: str) -> str:
        if not file: return None
        ext = os.path.splitext(file.filename)[1]
        filename = f"{prefix}_{user_id}_{uuid4().hex[:8]}{ext}"
        filepath = os.path.join(settings.upload_dir, filename)
        content = await file.read()
        with open(filepath, "wb") as f:
            f.write(content)
        return f"/uploads/{filename}"

    if enrollment_certificate:
        advocate.enrollment_certificate_path = await save_file(enrollment_certificate, "enrollment")
    if pan_document:
        advocate.pan_document_path = await save_file(pan_document, "pan")
    if gov_id:
        advocate.gov_id_path = await save_file(gov_id, "govid")
    if degree_certificate:
        advocate.degree_certificate_path = await save_file(degree_certificate, "degree")
    if certificate_of_practice:
        advocate.certificate_of_practice_path = await save_file(certificate_of_practice, "cop")
        
    await db.commit()
    return success_response(message="Documents uploaded successfully")


@router.post("/onboarding/submit", response_model=dict)
async def submit_for_verification(
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(get_current_user_token)
):
    """Final Step: Submit profile for admin review"""
    user_id = token_data.get("sub")
    query = select(Advocate).where(Advocate.user_id == user_id)
    result = await db.execute(query)
    advocate = result.scalars().first()
    
    if not advocate:
        raise HTTPException(status_code=404, detail="Profile not found")
        
    advocate.verification_status = "under_review"
    
    await db.commit()
    return success_response(message="Profile submitted for verification")


@router.get("/admin/all", response_model=dict)
async def get_all_advocate_profiles(
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(get_current_user_token)
):
    """Admin only: Get all advocate profiles with their verification status"""
    if token_data.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view this")
        
    from app.models.user import User
    
    query = select(Advocate, User).join(User, Advocate.user_id == User.id)
    result = await db.execute(query)
    
    data = []
    for adv, user in result.all():
        profile = AdvocateProfileResponse.model_validate(adv).model_dump(mode='json')
        profile['first_name'] = user.first_name
        profile['last_name'] = user.last_name
        profile['email'] = user.email
        profile['is_active'] = user.is_active
        data.append(profile)
        
    return success_response(message="Advocate profiles retrieved", data=data)


@router.post("/admin/{user_id}/verify", response_model=dict)
async def verify_advocate_profile(
    user_id: str,
    payload: VerificationStatusUpdate,
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(get_current_user_token)
):
    """Admin only: Approve or reject an advocate's profile"""
    if token_data.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can perform this action")
        
    query = select(Advocate).where(Advocate.user_id == user_id)
    result = await db.execute(query)
    advocate = result.scalars().first()
    
    if not advocate:
        raise HTTPException(status_code=404, detail="Advocate profile not found")
        
    advocate.verification_status = payload.verification_status
    if payload.verification_status == "approved":
        advocate.is_available = True
        
    await db.commit()
    return success_response(message=f"Advocate profile marked as {payload.verification_status}")
