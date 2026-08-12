"""
Legal AI System - Payment Model
=================================
Stores payment transactions linked to cases.
Supports Razorpay integration.
"""

import enum
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class PaymentStatus(str, enum.Enum):
    """Payment status values."""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentMethod(str, enum.Enum):
    """Supported payment methods."""
    UPI = "upi"
    DEBIT_CARD = "debit_card"
    CREDIT_CARD = "credit_card"
    NET_BANKING = "net_banking"
    WALLET = "wallet"


class Payment(BaseModel):
    """
    Payment table.
    
    Records all payment transactions.
    Integrates with Razorpay for order creation and verification.
    """
    __tablename__ = "payments"

    case_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Foreign key to cases table",
    )
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Foreign key to clients table",
    )
    amount = Column(
        Numeric(10, 2),
        nullable=False,
        comment="Payment amount",
    )
    currency = Column(
        String(10),
        default="INR",
        nullable=False,
        comment="Payment currency (ISO 4217)",
    )
    payment_method = Column(
        Enum(PaymentMethod, name="payment_method_enum", create_constraint=True),
        nullable=True,
        comment="Payment method used",
    )
    razorpay_order_id = Column(
        String(100),
        nullable=True,
        unique=True,
        comment="Razorpay order ID",
    )
    razorpay_payment_id = Column(
        String(100),
        nullable=True,
        unique=True,
        comment="Razorpay payment ID (received after successful payment)",
    )
    razorpay_signature = Column(
        String(255),
        nullable=True,
        comment="Razorpay payment signature for verification",
    )
    status = Column(
        Enum(PaymentStatus, name="payment_status_enum", create_constraint=True),
        default=PaymentStatus.PENDING,
        nullable=False,
        index=True,
        comment="Payment status",
    )
    metadata_info = Column(
        "metadata",
        JSONB,
        nullable=True,
        comment="Additional payment metadata",
    )
    paid_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When payment was completed",
    )

    # --- Relationships ---
    case = relationship("Case", back_populates="payments")
    client = relationship("Client", back_populates="payments")

    def __repr__(self):
        return f"<Payment(amount={self.amount}, status='{self.status}')>"
