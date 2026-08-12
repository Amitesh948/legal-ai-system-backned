"""
Legal AI System - Case Message Model
======================================
Stores chat messages between clients and advocates for a specific case.
"""

from sqlalchemy import Column, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class CaseMessage(BaseModel):
    """
    Message table for case-specific chat.
    """
    __tablename__ = "case_messages"

    case_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="The user who sent the message",
    )
    message_text = Column(
        Text,
        nullable=False,
        comment="The content of the message",
    )
    is_read = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Has the recipient read it?",
    )

    # Relationships
    case = relationship("Case", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])

    def __repr__(self):
        return f"<CaseMessage(id={self.id}, case_id={self.case_id}, sender_id={self.sender_id})>"
