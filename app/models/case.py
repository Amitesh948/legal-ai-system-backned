"""
Legal AI System - Case Model
==============================
Core case management table with status tracking.
"""

import enum

from sqlalchemy import Column, Date, Enum, ForeignKey, String, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class CaseStatus(str, enum.Enum):
    """Case lifecycle status values."""
    NEW = "new"
    PAYMENT_PENDING = "payment_pending"
    PAYMENT_COMPLETED = "payment_completed"
    PAYMENT_FAILED = "payment_failed"
    DOCUMENTS_UPLOADED = "documents_uploaded"
    AI_PROCESSING = "ai_processing"
    UNDER_REVIEW = "under_review"
    OPINION_GENERATED = "opinion_generated"
    REPORT_GENERATED = "report_generated"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CasePriority(str, enum.Enum):
    """Case priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Case(BaseModel):
    """
    Case table - central entity in the system.
    
    A case is created by a client, assigned to an advocate,
    processed through the AI pipeline, and results in a legal opinion report.
    
    Status transitions follow the state machine defined in CaseStatus.
    """
    __tablename__ = "cases"

    case_number = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Auto-generated case reference number (e.g., CASE-2026-0001)",
    )
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Foreign key to clients table",
    )
    advocate_id = Column(
        UUID(as_uuid=True),
        ForeignKey("advocates.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Foreign key to advocates table (assigned later)",
    )
    title = Column(
        String(300),
        nullable=False,
        comment="Brief case title",
    )
    description = Column(
        Text,
        nullable=True,
        comment="Detailed case description from client",
    )
    client_rating = Column(Integer, nullable=True, comment="Client rating (1-5)")
    client_review = Column(Text, nullable=True, comment="Client feedback review")
    case_type = Column(
        String(100),
        nullable=True,
        comment="Type of case (civil, criminal, family, corporate, etc.)",
    )
    status = Column(
        Enum(CaseStatus, name="case_status_enum", create_constraint=True, values_callable=lambda x: [e.value for e in x]),
        default=CaseStatus.NEW,
        nullable=False,
        index=True,
        comment="Current case status",
    )
    priority = Column(
        Enum(CasePriority, name="case_priority_enum", create_constraint=True, values_callable=lambda x: [e.value for e in x]),
        default=CasePriority.MEDIUM,
        nullable=False,
        comment="Case priority level",
    )
    court_name = Column(
        String(200),
        nullable=True,
        comment="Name of the court (if applicable)",
    )
    next_hearing_date = Column(
        Date,
        nullable=True,
        comment="Next court hearing date",
    )

    # --- Relationships ---
    client = relationship("Client", back_populates="cases")
    advocate = relationship("Advocate", back_populates="cases")
    documents = relationship("CaseDocument", back_populates="case", lazy="selectin", cascade="all, delete-orphan")
    ai_summary = relationship("AISummary", back_populates="case", uselist=False, lazy="selectin", cascade="all, delete-orphan")
    legal_opinion = relationship("LegalOpinion", back_populates="case", uselist=False, lazy="selectin", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="case", lazy="dynamic", cascade="all, delete-orphan")
    report = relationship("Report", back_populates="case", uselist=False, lazy="selectin", cascade="all, delete-orphan")
    status_history = relationship("CaseStatusHistory", back_populates="case", lazy="dynamic", cascade="all, delete-orphan")

    messages = relationship("CaseMessage", back_populates="case", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Case(case_number='{self.case_number}', status='{self.status}')>"
