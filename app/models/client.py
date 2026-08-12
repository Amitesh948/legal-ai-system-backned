"""
Legal AI System - Client Model
================================
Extended profile for users with the 'client' role.
"""

from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Client(BaseModel):
    """
    Client profile table.
    
    One-to-one relationship with User (role=client).
    Stores additional personal/legal information needed for case management.
    """
    __tablename__ = "clients"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
        comment="Foreign key to users table",
    )
    address = Column(
        String(500),
        nullable=True,
        comment="Full postal address",
    )
    city = Column(
        String(100),
        nullable=True,
        comment="City name",
    )
    state = Column(
        String(100),
        nullable=True,
        comment="State/Province",
    )
    pincode = Column(
        String(10),
        nullable=True,
        comment="PIN/ZIP code",
    )
    aadhar_number = Column(
        String(20),
        nullable=True,
        comment="Aadhar card number (encrypted at rest)",
    )
    pan_number = Column(
        String(20),
        nullable=True,
        comment="PAN card number",
    )
    notes = Column(
        Text,
        nullable=True,
        comment="Internal notes about the client",
    )

    # --- Relationships ---
    user = relationship("User", back_populates="client_profile")
    cases = relationship("Case", back_populates="client", lazy="dynamic")
    payments = relationship("Payment", back_populates="client", lazy="dynamic")

    def __repr__(self):
        return f"<Client(user_id='{self.user_id}')>"
