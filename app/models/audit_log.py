"""
Legal AI System - Audit Log Model
====================================
Immutable audit trail for security compliance.
Tracks all state-changing actions in the system.
"""

from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class AuditLog(BaseModel):
    """
    Audit log table.
    
    Immutable record of every state-changing action.
    Used for security compliance and debugging.
    Stores old/new values for data change tracking.
    """
    __tablename__ = "audit_logs"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="User who performed the action",
    )
    action = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Action performed (create, update, delete, login, logout, etc.)",
    )
    resource_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Type of resource affected (user, case, payment, etc.)",
    )
    resource_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="ID of the affected resource",
    )
    ip_address = Column(
        String(45),
        nullable=True,
        comment="Client IP address (supports IPv6)",
    )
    user_agent = Column(
        Text,
        nullable=True,
        comment="Client user agent string",
    )
    old_values = Column(
        JSONB,
        nullable=True,
        comment="Previous values before the change",
    )
    new_values = Column(
        JSONB,
        nullable=True,
        comment="New values after the change",
    )

    # --- Relationships ---
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog(action='{self.action}', resource='{self.resource_type}')>"
