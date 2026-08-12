"""
Legal AI System - User Model
==============================
Core user table for authentication and profile.
Links to Role, Client profile, or Advocate profile.
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class User(BaseModel):
    """
    User table - stores authentication and basic profile data.
    
    Each user has exactly one role (admin/advocate/client).
    Depending on role, a user may have a linked Client or Advocate profile.
    """
    __tablename__ = "users"

    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="User email address (used for login)",
    )
    password_hash = Column(
        String(255),
        nullable=False,
        comment="Bcrypt hashed password",
    )
    first_name = Column(
        String(100),
        nullable=False,
        comment="User first name",
    )
    last_name = Column(
        String(100),
        nullable=False,
        comment="User last name",
    )
    phone = Column(
        String(20),
        nullable=True,
        comment="Phone number with country code",
    )
    role_id = Column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Foreign key to roles table",
    )
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether the user account is active",
    )
    is_verified = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether the user email is verified",
    )
    reset_token = Column(
        String(255),
        nullable=True,
        comment="Password reset token",
    )
    reset_token_expires = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Password reset token expiry",
    )
    refresh_token = Column(
        String(500),
        nullable=True,
        comment="Hashed refresh token for token rotation",
    )
    preferences = Column(
        JSON,
        nullable=False,
        default=dict,
        server_default='{}',
        comment="JSON object storing user specific settings (e.g., email_notifications)",
    )

    # --- Relationships ---
    role = relationship("Role", back_populates="users", lazy="selectin")
    client_profile = relationship(
        "Client", back_populates="user", uselist=False, lazy="selectin"
    )
    advocate_profile = relationship(
        "Advocate", back_populates="user", uselist=False, lazy="selectin"
    )
    notifications = relationship("Notification", back_populates="user", lazy="dynamic")
    audit_logs = relationship("AuditLog", back_populates="user", lazy="dynamic")

    @property
    def full_name(self) -> str:
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<User(email='{self.email}', role_id='{self.role_id}')>"
