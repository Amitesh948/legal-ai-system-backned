from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from app.database.session import get_db
from app.core.security import get_current_user_token
from app.api.common.responses import success_response
from app.models.report import Report
from app.models.case import Case
from app.models.client import Client
from app.models.advocate import Advocate
from app.api.v1.reports.schemas import ReportResponse

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("", response_model=dict)
async def get_my_reports(
    token_data: dict = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all reports for the logged-in user.
    If client: returns reports for their cases.
    If advocate: returns reports for cases assigned to them.
    """
    user_id = UUID(token_data.get("sub"))
    role = token_data.get("role")
    
    # Base query joining Case
    query = select(Report, Case).join(Case, Report.case_id == Case.id)
    
    if role == "client":
        # Find client profile
        client_result = await db.execute(select(Client).where(Client.user_id == user_id))
        client = client_result.scalars().first()
        if not client:
            return success_response(data=[])
        query = query.where(Case.client_id == client.id)
        
    elif role == "advocate":
        # Find advocate profile
        adv_result = await db.execute(select(Advocate).where(Advocate.user_id == user_id))
        advocate = adv_result.scalars().first()
        if not advocate:
            return success_response(data=[])
        query = query.where(Case.advocate_id == advocate.id)
        
    query = query.order_by(Report.created_at.desc())
    
    result = await db.execute(query)
    rows = result.all()
    
    reports_data = []
    for report, case in rows:
        report_dict = ReportResponse.model_validate(report).model_dump()
        report_dict["case_number"] = case.case_number if hasattr(case, "case_number") else str(case.id)[:8]
        reports_data.append(report_dict)
        
    return success_response(data=reports_data)
