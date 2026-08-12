"""
Legal AI System - Report Model
================================
Stores generated PDF reports linked to cases.
"""

import enum

from sqlalchemy import Boolean, Column, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class ReportStatus(str, enum.Enum):
    """Report generation status."""
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class Report(BaseModel):
    """
    Report table.
    
    Stores metadata for generated PDF legal opinion reports.
    One-to-one relationship with Case.
    """
    __tablename__ = "reports"

    case_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
        comment="Foreign key to cases table (one report per case)",
    )
    generated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who generated the report",
    )
    report_type = Column(
        String(50),
        default="legal_opinion",
        nullable=False,
        comment="Type of report (legal_opinion, consultation, etc.)",
    )
    file_path = Column(
        String(500),
        nullable=True,
        comment="Path to the generated PDF file",
    )
    file_name = Column(
        String(255),
        nullable=True,
        comment="Generated PDF file name",
    )
    has_signature = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether the report includes a digital signature",
    )
    has_watermark = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether the report includes a watermark",
    )
    status = Column(
        Enum(ReportStatus, name="report_status_enum", create_constraint=True),
        default=ReportStatus.GENERATING,
        nullable=False,
        comment="Report generation status",
    )
    metadata_info = Column(
        "metadata",
        JSONB,
        nullable=True,
        comment="Additional report metadata (page count, generation time, etc.)",
    )

    # --- Relationships ---
    case = relationship("Case", back_populates="report")
    generator = relationship("User", foreign_keys=[generated_by])

    def __repr__(self):
        return f"<Report(case_id='{self.case_id}', status='{self.status}')>"
