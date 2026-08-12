"""
Legal AI System - Case Status History Model
=============================================
Tracks every status change for a case (full audit trail).
"""

from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class CaseStatusHistory(BaseModel):
    """
    Case status history table.
    
    Records every status transition for a case.
    Provides a complete timeline of case progress.
    """
    __tablename__ = "case_status_history"

    case_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key to cases table",
    )
    changed_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="User who triggered the status change",
    )
    old_status = Column(
        String(50),
        nullable=True,
        comment="Previous status value",
    )
    new_status = Column(
        String(50),
        nullable=False,
        comment="New status value",
    )
    remarks = Column(
        Text,
        nullable=True,
        comment="Remarks or reason for the status change",
    )

    # --- Relationships ---
    case = relationship("Case", back_populates="status_history")
    changed_by_user = relationship("User", foreign_keys=[changed_by])

    def __repr__(self):
        return f"<CaseStatusHistory(case_id='{self.case_id}', {self.old_status} -> {self.new_status})>"
