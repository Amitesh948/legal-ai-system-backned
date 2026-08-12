"""
Legal AI System - Notification Helper
=========================================
Utility functions to check user notification preferences
before sending emails, SMS, or other notifications.

This ensures the Settings page toggles are actually respected
by the backend when triggering notifications.
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger(__name__)


async def should_send_email(db: AsyncSession, user_id: str) -> bool:
    """
    Check if a user has email notifications enabled.
    
    Reads the `preferences` JSON column from the `users` table.
    Defaults to True (send emails) if:
    - The user has no preferences saved yet.
    - The `emailNotifications` key is missing.
    
    Args:
        db: Active database session.
        user_id: UUID string of the user.
        
    Returns:
        True if emails should be sent, False if user opted out.
    """
    try:
        from app.models.user import User
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        
        if not user:
            logger.warning(f"User {user_id} not found. Defaulting to send email.")
            return True
        
        preferences = user.preferences or {}
        enabled = preferences.get("emailNotifications", True)
        
        if not enabled:
            logger.info(f"Email notifications disabled for user {user_id}. Skipping email.")
        
        return enabled
        
    except Exception as e:
        logger.error(f"Error checking email preference for user {user_id}: {e}")
        # On error, default to sending (fail-open for notifications)
        return True


async def should_send_sms(db: AsyncSession, user_id: str) -> bool:
    """
    Check if a user has SMS notifications enabled.
    
    Defaults to False (don't send) since SMS requires explicit opt-in.
    
    Args:
        db: Active database session.
        user_id: UUID string of the user.
        
    Returns:
        True if SMS should be sent, False otherwise.
    """
    try:
        from app.models.user import User
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        
        if not user:
            return False
        
        preferences = user.preferences or {}
        return preferences.get("smsNotifications", False)
        
    except Exception as e:
        logger.error(f"Error checking SMS preference for user {user_id}: {e}")
        return False
