"""
Legal AI System - Legal Opinion Model
========================================
Stores advocate's legal opinion and analysis for a case.
"""

import enum

from sqlalchemy import Column, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class OpinionStatus(str, enum.Enum):
    """Legal opinion workflow status."""
    DRAFT = "draft"
    FINALIZED = "finalized"


class LegalOpinion(BaseModel):
    """
    Legal opinion table.
    
    Stores the advocate's review, edited AI summary, legal opinion,
    winning probability, and risk assessment.
    One-to-one relationship with Case.
    """
    __tablename__ = "legal_opinions"

    case_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
        comment="Foreign key to cases table (one opinion per case)",
    )
    advocate_id = Column(
        UUID(as_uuid=True),
        ForeignKey("advocates.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Advocate who wrote the opinion",
    )
    ai_summary_edited = Column(
        Text,
        nullable=True,
        comment="Advocate's edited version of the AI summary",
    )
    legal_opinion = Column(
        Text,
        nullable=True,
        comment="Advocate's legal opinion and analysis",
    )
    winning_probability = Column(
        Integer,
        nullable=True,
        comment="Estimated winning probability (0-100%)",
    )
    risk_assessment = Column(
        Text,
        nullable=True,
        comment="Risk analysis and potential challenges",
    )
    recommended_actions = Column(
        Text,
        nullable=True,
        comment="Recommended next steps for the client",
    )
    status = Column(
        Enum(OpinionStatus, name="opinion_status_enum", create_constraint=True),
        default=OpinionStatus.DRAFT,
        nullable=False,
        comment="Opinion status (draft or finalized)",
    )

    # --- Relationships ---
    case = relationship("Case", back_populates="legal_opinion")
    advocate = relationship("Advocate", back_populates="legal_opinions")

    def __repr__(self):
        return f"<LegalOpinion(case_id='{self.case_id}', status='{self.status}')>"
