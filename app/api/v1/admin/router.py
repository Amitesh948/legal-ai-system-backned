from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.security import get_current_user_token
from app.database.session import get_db
from app.api.common.responses import success_response
from app.models.user import User
from app.models.case import Case, CaseStatus
from app.models.payment import Payment, PaymentStatus
from app.models.client import Client

from app.models.audit_log import AuditLog

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])

@router.get("/stats")
async def get_admin_stats(
    token_data: dict = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Get top-level statistics for the admin dashboard.
    Only accessible by users with 'admin' role.
    """
    if token_data.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can access these statistics"
        )
        
    # 1. Total Clients
    clients_result = await db.execute(
        select(func.count(User.id)).where(User.role == "client")
    )
    total_clients = clients_result.scalar() or 0
    
    # 2. Total Advocates
    advocates_result = await db.execute(
        select(func.count(User.id)).where(User.role == "advocate")
    )
    total_advocates = advocates_result.scalar() or 0
    
    # 3. Total Active Cases
    active_cases_result = await db.execute(
        select(func.count(Case.id)).where(
            Case.status.not_in([CaseStatus.COMPLETED, CaseStatus.CANCELLED])
        )
    )
    total_active_cases = active_cases_result.scalar() or 0
    
    # 4. Total Revenue (Successful payments)
    revenue_result = await db.execute(
        select(func.sum(Payment.amount)).where(Payment.status == PaymentStatus.SUCCESS)
    )
    total_revenue = float(revenue_result.scalar() or 0)
    
    return success_response(
        data={
            "totalClients": total_clients,
            "totalAdvocates": total_advocates,
            "totalActiveCases": total_active_cases,
            "totalRevenue": total_revenue
        },
        message="Admin statistics retrieved successfully"
    )

@router.get("/activity")
async def get_admin_activity(
    token_data: dict = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the recent activity feed from Audit Logs for the admin dashboard.
    """
    if token_data.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can access activity logs"
        )
        
    # Fetch latest 20 audit logs with user details
    stmt = (
        select(AuditLog, User.first_name, User.last_name, User.role)
        .outerjoin(User, AuditLog.user_id == User.id)
        .order_by(AuditLog.created_at.desc())
        .limit(20)
    )
    
    result = await db.execute(stmt)
    rows = result.all()
    
    activity_feed = []
    for log, first_name, last_name, role in rows:
        user_name = f"{first_name} {last_name}" if first_name else "System"
        role_label = role.capitalize() if role else "System"
        
        # Determine exactly what message to show
        message = ""
        action = log.action.upper()
        
        # Parse common actions into readable English
        if "LOGIN" in action:
            message = f"logged into the system"
        elif "PAYMENT_COMPLETED" in action:
            details = log.new_values.get("details", "") if log.new_values else ""
            message = details if details else "completed a payment"
        elif "REPORT_GENERATED" in action or action == "UPDATE_CASE":
            if log.new_values and log.new_values.get("status") == "report_generated":
                message = "generated the final legal opinion report"
            else:
                message = f"updated a {log.resource_type}"
        elif action == "CREATE":
            message = f"created a new {log.resource_type}"
        else:
            message = f"performed {action} on {log.resource_type}"
            
        activity_feed.append({
            "id": str(log.id),
            "user_name": user_name,
            "user_role": role_label,
            "action_message": f"{user_name} ({role_label}) {message}",
            "resource_type": log.resource_type,
            "timestamp": log.created_at.isoformat()
        })
        
    return success_response(
        data=activity_feed,
        message="Recent activity retrieved successfully"
    )

@router.get("/clients")
async def get_admin_clients(
    token_data: dict = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all clients with their case counts for the admin directory.
    """
    if token_data.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can access the client directory"
        )
        
    # 1. Fetch all users with role 'client'
    stmt = select(User).where(User.role.has(name="client")).order_by(User.created_at.desc())
    result = await db.execute(stmt)
    users = result.scalars().all()
    
    clients_data = []
    
    if users:
        user_ids = [u.id for u in users]
        
        # 2. Fetch corresponding Client profiles
        client_stmt = select(Client.id, Client.user_id).where(Client.user_id.in_(user_ids))
        client_res = await db.execute(client_stmt)
        client_mapping = {row.user_id: row.id for row in client_res.all()}
        
        client_ids = list(client_mapping.values())
        
        # 3. Fetch case counts per client
        case_counts = {}
        if client_ids:
            case_stmt = select(Case.client_id, func.count(Case.id)).where(Case.client_id.in_(client_ids)).group_by(Case.client_id)
            case_res = await db.execute(case_stmt)
            for row in case_res.all():
                case_counts[row[0]] = row[1]
                
        # 4. Assemble the data
        for user in users:
            c_id = client_mapping.get(user.id)
            c_count = case_counts.get(c_id, 0) if c_id else 0
            
            clients_data.append({
                "user_id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "name": f"{user.first_name} {user.last_name}",
                "case_count": c_count,
                "joined_at": user.created_at.isoformat() if user.created_at else None
            })
            
    return success_response(
        data=clients_data,
        message="Client directory retrieved successfully"
    )

@router.get("/payments")
async def get_admin_payments(
    token_data: dict = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all financial transactions for the admin ledger.
    """
    if token_data.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can access financial records"
        )
        
    stmt = (
        select(
            Payment.id,
            Payment.amount,
            Payment.currency,
            Payment.status,
            Payment.razorpay_order_id,
            Payment.razorpay_payment_id,
            Payment.created_at,
            Case.title.label("case_title"),
            User.first_name,
            User.last_name,
            User.email
        )
        .outerjoin(Case, Case.id == Payment.case_id)
        .outerjoin(Client, Client.id == Payment.client_id)
        .outerjoin(User, User.id == Client.user_id)
        .order_by(Payment.created_at.desc())
    )
    
    result = await db.execute(stmt)
    rows = result.all()
    
    payments = []
    for row in rows:
        payments.append({
            "payment_id": str(row.id),
            "amount": float(row.amount),
            "currency": row.currency,
            "status": row.status,
            "order_id": row.razorpay_order_id,
            "transaction_id": row.razorpay_payment_id or "N/A",
            "date": row.created_at.isoformat() if row.created_at else None,
            "case_title": row.case_title or "N/A",
            "client_name": f"{row.first_name} {row.last_name}" if row.first_name else "Unknown",
            "client_email": row.email or "Unknown"
        })
        
    return success_response(
        data=payments,
        message="Financial ledger retrieved successfully"
    )
