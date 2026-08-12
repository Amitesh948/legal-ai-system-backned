"""
Legal AI System - AI Summary Model
=====================================
Stores structured AI-generated analysis for each case.
"""

import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class AISummaryStatus(str, enum.Enum):
    """AI processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AISummary(BaseModel):
    """
    AI summary table.
    
    Stores the structured JSON output from the AI analysis.
    One-to-one relationship with Case.
    Uses JSONB columns for flexible, queryable structured data.
    """
    __tablename__ = "ai_summaries"

    case_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
        comment="Foreign key to cases table (one summary per case)",
    )
    summary = Column(
        JSONB,
        nullable=True,
        comment="AI-generated case summary",
    )
    important_facts = Column(
        JSONB,
        nullable=True,
        comment="Array of key facts identified by AI",
    )
    timeline = Column(
        JSONB,
        nullable=True,
        comment="Array of {date, event} objects",
    )
    legal_issues = Column(
        JSONB,
        nullable=True,
        comment="Array of identified legal issues",
    )
    suggested_sections = Column(
        JSONB,
        nullable=True,
        comment="Array of relevant legal sections and acts",
    )
    suggested_actions = Column(
        JSONB,
        nullable=True,
        comment="Array of recommended actions",
    )
    precedents = Column(
        JSONB,
        nullable=True,
        comment="Array of potentially relevant case precedents",
    )
    raw_response = Column(
        Text,
        nullable=True,
        comment="Raw AI API response for debugging",
    )
    model_used = Column(
        String(50),
        nullable=True,
        comment="AI model used (gpt-4, claude-3, etc.)",
    )
    status = Column(
        Enum(AISummaryStatus, name="ai_summary_status_enum", create_constraint=True),
        default=AISummaryStatus.PENDING,
        nullable=False,
        comment="Processing status",
    )
    processed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When AI processing completed",
    )

    # --- Relationships ---
    case = relationship("Case", back_populates="ai_summary")

    def __repr__(self):
        return f"<AISummary(case_id='{self.case_id}', status='{self.status}')>"
