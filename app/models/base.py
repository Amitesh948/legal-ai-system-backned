"""
Legal AI System - Base Model
==============================
Abstract base model with common fields shared by all tables.
Every model inherits from this to get id, created_at, updated_at automatically.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID

from app.database.session import Base


class BaseModel(Base):
    """
    Abstract base model providing:
    - UUID primary key
    - created_at timestamp (auto-set on insert)
    - updated_at timestamp (auto-set on insert and update)
    
    All models in the system inherit from this class.
    """
    __abstract__ = True

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        comment="Unique identifier (UUID v4)",
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Record creation timestamp",
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Record last update timestamp",
    )
