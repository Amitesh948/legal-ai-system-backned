"""
Legal AI System - Models Package
==================================
Central import point for all SQLAlchemy models.
Alembic and the application use this to discover all tables.
"""

# Base must be imported first
from app.models.base import BaseModel

# Import all models so SQLAlchemy registers them
from app.models.role import Role
from app.models.user import User
from app.models.client import Client
from app.models.advocate import Advocate
from app.models.case import Case, CaseStatus, CasePriority
from app.models.case_document import CaseDocument
from app.models.ai_summary import AISummary, AISummaryStatus
from app.models.legal_opinion import LegalOpinion, OpinionStatus
from app.models.payment import Payment, PaymentStatus, PaymentMethod
from app.models.report import Report, ReportStatus
from app.models.citation import Citation
from app.models.notification import Notification
from app.models.audit_log import AuditLog
from app.models.case_status_history import CaseStatusHistory
from app.models.otp import OTPVerification
from app.models.case_message import CaseMessage


# All models listed for easy reference
__all__ = [
    "BaseModel",
    "Role",
    "User",
    "Client",
    "Advocate",
    "Case",
    "CaseStatus",
    "CasePriority",
    "CaseDocument",
    "AISummary",
    "AISummaryStatus",
    "LegalOpinion",
    "OpinionStatus",
    "Payment",
    "PaymentStatus",
    "PaymentMethod",
    "Report",
    "ReportStatus",
    "Citation",
    "Notification",
    "AuditLog",
    "CaseStatusHistory",
    "OTPVerification",
]
