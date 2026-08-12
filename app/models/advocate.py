"""
Legal AI System - Advocate Model
==================================
Extended profile for users with the 'advocate' role.
"""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Advocate(BaseModel):
    """
    Advocate profile table.
    
    One-to-one relationship with User (role=advocate).
    Stores professional details: bar council ID, specialization, signature, etc.
    """
    __tablename__ = "advocates"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
        comment="Foreign key to users table",
    )
    # --- Professional Details ---
    state = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    bar_association = Column(String(200), nullable=True)
    practice_areas = Column(String(500), nullable=True)
    
    # --- Legal Education ---
    llb_degree = Column(String(200), nullable=True)
    university = Column(String(200), nullable=True)
    college = Column(String(200), nullable=True)
    graduation_year = Column(Integer, nullable=True)
    degree_certificate_path = Column(String(500), nullable=True)
    
    # --- Bar Council Details ---
    state_bar_council = Column(String(200), nullable=True)
    bar_council_id = Column(String(50), unique=True, nullable=True, index=True)
    enrollment_date = Column(String(50), nullable=True)
    enrollment_certificate_path = Column(String(500), nullable=True)
    aibe_status = Column(String(50), nullable=True, default="pending")
    certificate_of_practice_path = Column(String(500), nullable=True)
    
    # --- Identity Verification ---
    pan_number = Column(String(20), nullable=True)
    pan_document_path = Column(String(500), nullable=True)
    gov_id_path = Column(String(500), nullable=True)
    photograph_path = Column(String(500), nullable=True)
    
    # --- Professional Verification & Status ---
    verification_status = Column(String(50), default="pending", server_default="pending", nullable=False, index=True)
    is_available = Column(Boolean, default=False, server_default="false", nullable=False)
    
    # Legacy fields
    experience_years = Column(Integer, nullable=True, default=0)
    bio = Column(Text, nullable=True)
    signature_image = Column(String(500), nullable=True)

    # --- Relationships ---
    user = relationship("User", back_populates="advocate_profile")
    cases = relationship("Case", back_populates="advocate", lazy="dynamic")
    legal_opinions = relationship("LegalOpinion", back_populates="advocate", lazy="dynamic")
    citations = relationship("Citation", back_populates="added_by_advocate", lazy="dynamic")

    def __repr__(self):
        return f"<Advocate(bar_council_id='{self.bar_council_id}')>"
