from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.database.session import get_db
from app.core.security import get_current_user_token
from app.api.common.responses import success_response
from app.repositories.notification_repository import notification_repository
from app.api.v1.notifications.schemas import NotificationResponse, UnreadCountResponse

router = APIRouter()

@router.get("", response_model=dict)
async def get_notifications(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(get_current_user_token)
):
    """Get all notifications for the current user."""
    user_id = UUID(token_data.get("sub"))
    notifications = await notification_repository.get_by_user(db, user_id, skip=skip, limit=limit)
    
    # Convert to schema format
    return success_response(
        message="Notifications retrieved successfully",
        data=[NotificationResponse.model_validate(n).model_dump() for n in notifications]
    )

@router.get("/unread-count", response_model=dict)
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(get_current_user_token)
):
    """Get count of unread notifications for the current user."""
    user_id = UUID(token_data.get("sub"))
    count = await notification_repository.get_unread_count(db, user_id)
    return success_response(
        message="Unread count retrieved successfully",
        data={"unread_count": count}
    )

@router.patch("/{notification_id}/read", response_model=dict)
async def mark_as_read(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(get_current_user_token)
):
    """Mark a specific notification as read."""
    user_id = UUID(token_data.get("sub"))
    notification = await notification_repository.mark_as_read(db, notification_id, user_id)
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
        
    return success_response(
        message="Notification marked as read",
        data=NotificationResponse.model_validate(notification).model_dump()
    )

@router.patch("/read-all", response_model=dict)
async def mark_all_as_read(
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(get_current_user_token)
):
    """Mark all notifications as read for the current user."""
    user_id = UUID(token_data.get("sub"))
    updated_count = await notification_repository.mark_all_as_read(db, user_id)
    
    return success_response(
        message=f"{updated_count} notifications marked as read",
        data={"updated_count": updated_count}
    )
