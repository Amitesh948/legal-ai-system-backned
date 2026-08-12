from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from app.models.payment import PaymentStatus, PaymentMethod

class PaymentCreate(BaseModel):
    case_id: UUID = Field(..., description="The ID of the case this payment is for")
    amount: float = Field(..., gt=0, description="Payment amount in INR")
    currency: str = Field(default="INR")

class PaymentOrderResponse(BaseModel):
    id: UUID
    case_id: UUID
    amount: float
    currency: str
    razorpay_order_id: str
    status: PaymentStatus
    created_at: datetime

    class Config:
        from_attributes = True

class PaymentVerify(BaseModel):
    razorpay_order_id: str = Field(..., description="Razorpay Order ID")
    razorpay_payment_id: str = Field(..., description="Razorpay Payment ID")
    razorpay_signature: str = Field(..., description="Razorpay Signature")

class PaymentResponse(BaseModel):
    id: UUID
    case_id: UUID
    client_id: UUID
    amount: float
    currency: str
    payment_method: Optional[PaymentMethod] = None
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    status: PaymentStatus
    paid_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
