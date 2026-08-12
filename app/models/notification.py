"""
Legal AI System - Notification Model
=======================================
Stores in-app and email notifications for users.
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Notification(BaseModel):
    """
    Notification table.
    
    Stores all notifications sent to users.
    Supports multiple channels (email, in-app, future: WhatsApp, SMS).
    """
    __tablename__ = "notifications"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Recipient user ID",
    )
    type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Notification type (case_update, payment, report_ready, etc.)",
    )
    title = Column(
        String(300),
        nullable=False,
        comment="Notification title",
    )
    message = Column(
        Text,
        nullable=False,
        comment="Notification message body",
    )
    channel = Column(
        String(20),
        default="in_app",
        nullable=False,
        comment="Delivery channel (in_app, email, whatsapp, sms)",
    )
    is_read = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Whether notification has been read",
    )
    metadata_info = Column(
        "metadata",
        JSONB,
        nullable=True,
        comment="Additional data (case_id, payment_id, etc.)",
    )
    read_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the notification was read",
    )

    # --- Relationships ---
    user = relationship("User", back_populates="notifications")

    def __repr__(self):
        return f"<Notification(type='{self.type}', user_id='{self.user_id}')>"
