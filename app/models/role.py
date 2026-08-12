"""
Legal AI System - Role Model
==============================
Defines user roles: admin, advocate, client.
"""

from sqlalchemy import Column, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Role(BaseModel):
    """
    Role table - defines system roles.
    
    Seeded roles:
    - admin: Full system access
    - advocate: Case review, report generation
    - client: Case submission, document upload
    """
    __tablename__ = "roles"

    name = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Role name (admin, advocate, client)",
    )
    description = Column(
        Text,
        nullable=True,
        comment="Role description",
    )
    permissions = Column(
        JSONB,
        nullable=True,
        default=dict,
        comment="JSON object defining granular permissions",
    )

    # --- Relationships ---
    users = relationship("User", back_populates="role", lazy="selectin")

    def __repr__(self):
        return f"<Role(name='{self.name}')>"
