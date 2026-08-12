"""
Legal AI System - V1 API Router
=================================
Aggregates all v1 module routers into a single router.
New modules are registered here as they are implemented.
"""

from fastapi import APIRouter

# Import module routers as they are implemented
from app.api.v1.auth.router import router as auth_router
from app.api.v1.cases.router import router as cases_router
from app.api.v1.citations.router import router as citations_router
from app.api.v1.payments.router import router as payments_router
from app.api.v1.advocates.router import router as advocates_router
from app.api.v1.notifications.router import router as notifications_router
from app.api.v1.reports.router import router as reports_router
from app.api.v1.dashboard.router import router as dashboard_router
from app.api.v1.admin.router import router as admin_router

# --- V1 API Router ---
api_v1_router = APIRouter()

# Register module routers
api_v1_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(cases_router, prefix="/cases", tags=["Case Management"])
api_v1_router.include_router(citations_router, prefix="/citations", tags=["Citations"])
api_v1_router.include_router(notifications_router, prefix="/notifications", tags=["Notifications"])
api_v1_router.include_router(payments_router) # prefix is defined in the payments_router directly as /payments
api_v1_router.include_router(advocates_router) # prefix is defined in advocates_router as /advocates
api_v1_router.include_router(reports_router) # prefix is defined in reports_router directly as /reports
api_v1_router.include_router(dashboard_router) # prefix is defined as /dashboard
api_v1_router.include_router(admin_router) # prefix is defined as /admin

# Future modules will be added here as implemented:
# api_v1_router.include_router(users_router, prefix="/users", tags=["Users"])
# api_v1_router.include_router(clients_router, prefix="/clients", tags=["Clients"])
# api_v1_router.include_router(cases_router, prefix="/cases", tags=["Cases"])
# api_v1_router.include_router(documents_router, prefix="/documents", tags=["Documents"])
# api_v1_router.include_router(payments_router, prefix="/payments", tags=["Payments"])
# api_v1_router.include_router(ai_router, prefix="/ai", tags=["AI"])
# api_v1_router.include_router(reports_router, prefix="/reports", tags=["Reports"])
# api_v1_router.include_router(citations_router, prefix="/citations", tags=["Citations"])
# api_v1_router.include_router(notifications_router, prefix="/notifications", tags=["Notifications"])
# api_v1_router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
