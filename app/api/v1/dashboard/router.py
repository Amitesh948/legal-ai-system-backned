from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database.session import get_db
from app.core.security import get_current_user_token
from app.api.common.responses import success_response
from app.api.v1.dashboard.schemas import AuditLogResponse
from app.repositories.audit_log_repository import audit_log_repo

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/audit-logs", response_model=dict)
async def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    token_data: dict = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Admin only: Get paginated audit logs.
    """
    if token_data.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
        
    logs = await audit_log_repo.get_logs_paginated(db, skip=skip, limit=limit)
    
    response_data = []
    for log in logs:
        log_dict = AuditLogResponse.model_validate(log).model_dump()
        log_dict["user_email"] = log.user.email if log.user else "Unknown"
        response_data.append(log_dict)
        
    return success_response(data=response_data)
