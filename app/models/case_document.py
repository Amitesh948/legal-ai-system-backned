"""
Legal AI System - Case Document Model
========================================
Stores uploaded documents linked to a case.
Tracks OCR processing status and extracted text.
"""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class CaseDocument(BaseModel):
    """
    Case document table.
    
    Stores metadata for uploaded files (PDF, DOCX, JPG, PNG).
    Tracks whether OCR has been performed and stores extracted text.
    Uses file_hash for duplicate detection.
    """
    __tablename__ = "case_documents"

    case_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key to cases table",
    )
    uploaded_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="User who uploaded the document",
    )
    file_name = Column(
        String(255),
        nullable=False,
        comment="Stored file name (UUID-based to prevent conflicts)",
    )
    original_name = Column(
        String(255),
        nullable=False,
        comment="Original file name as uploaded by user",
    )
    file_path = Column(
        String(500),
        nullable=False,
        comment="Full path to the stored file",
    )
    mime_type = Column(
        String(100),
        nullable=False,
        comment="MIME type (application/pdf, image/jpeg, etc.)",
    )
    file_size = Column(
        Integer,
        nullable=False,
        comment="File size in bytes",
    )
    file_hash = Column(
        String(64),
        nullable=False,
        index=True,
        comment="SHA-256 hash for duplicate detection",
    )
    document_type = Column(
        String(100),
        nullable=True,
        comment="Document category (contract, court_order, evidence, etc.)",
    )
    ocr_processed = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether OCR has been performed on this document",
    )
    extracted_text = Column(
        Text,
        nullable=True,
        comment="Text extracted from the document (via OCR or direct extraction)",
    )

    # --- Relationships ---
    case = relationship("Case", back_populates="documents")
    uploader = relationship("User", foreign_keys=[uploaded_by])

    def __repr__(self):
        return f"<CaseDocument(original_name='{self.original_name}', case_id='{self.case_id}')>"
