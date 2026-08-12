from datetime import datetime, timezone, timedelta
from sqlalchemy import String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel

class OTPVerification(BaseModel):
    """
    Stores OTPs for email verification before registration.
    """
    __tablename__ = "otp_verifications"

    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    otp_code: Mapped[str] = mapped_column(String(10), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at
