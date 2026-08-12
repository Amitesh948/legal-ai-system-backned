"""
Legal AI System - Citation Library Model
==========================================
Private legal reference database for advocates.
"""

from sqlalchemy import Column, Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Citation(BaseModel):
    """
    Citation library table.
    
    Private database for legal references: judgments, acts, sections.
    Only accessible by advocates and admins.
    Keywords stored as JSONB array for flexible search.
    """
    __tablename__ = "citation_library"

    added_by = Column(
        UUID(as_uuid=True),
        ForeignKey("advocates.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Advocate who added this citation",
    )
    title = Column(
        String(500),
        nullable=False,
        comment="Citation title or case name",
    )
    citation_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Type: judgment, act, section, article",
    )
    act_name = Column(
        String(300),
        nullable=True,
        comment="Name of the act (if applicable)",
    )
    section_number = Column(
        String(50),
        nullable=True,
        comment="Section number within the act",
    )
    judgment_text = Column(
        Text,
        nullable=True,
        comment="Full judgment text or excerpt",
    )
    court_name = Column(
        String(200),
        nullable=True,
        comment="Court that delivered the judgment",
    )
    judgment_date = Column(
        Date,
        nullable=True,
        comment="Date of the judgment",
    )
    case_reference = Column(
        String(200),
        nullable=True,
        comment="Case citation reference (e.g., AIR 2020 SC 1234)",
    )
    notes = Column(
        Text,
        nullable=True,
        comment="Advocate's personal notes on this citation",
    )
    keywords = Column(
        JSONB,
        nullable=True,
        default=list,
        comment="Array of keywords for search",
    )
    category = Column(
        String(100),
        nullable=True,
        index=True,
        comment="Category (criminal, civil, constitutional, etc.)",
    )

    # --- Relationships ---
    added_by_advocate = relationship("Advocate", back_populates="citations")

    def __repr__(self):
        return f"<Citation(title='{self.title[:50]}', type='{self.citation_type}')>"
