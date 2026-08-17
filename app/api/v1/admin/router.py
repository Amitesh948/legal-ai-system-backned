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

from pydantic import BaseModel

class BroadcastMessage(BaseModel):
    message: str
    type: str = "info"
    title: str = "System Announcement"

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])

@router.post("/broadcast")
async def send_global_broadcast(
    payload: BroadcastMessage,
    token_data: dict = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db)
):
    if token_data.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can send broadcasts")
        
    from app.services.websocket_manager import manager
    from app.models.notification import Notification
    from app.models.user import User
    
    # 1. Broadcast via WebSocket for immediate popups
    await manager.broadcast_to_case("global", {
        "type": "global_broadcast",
        "data": payload.model_dump()
    })
    
    # 2. Persist in database so offline users see it when they login
    from app.models.role import Role
    # Fetch all non-admin users
    users_query = select(User.id).join(User.role).where(Role.name.in_(["client", "advocate"]))
    result = await db.execute(users_query)
    user_ids = result.scalars().all()
    
    if user_ids:
        # Create a notification object for each user
        notifications = [
            Notification(
                user_id=uid,
                type="system_broadcast",
                title=payload.title,
                message=payload.message,
                channel="in_app",
                is_read=False
            )
            for uid in user_ids
        ]
        db.add_all(notifications)
        await db.commit()
    
    
    return success_response(message="Broadcast sent and saved to notifications")

class UserStatusUpdate(BaseModel):
    is_active: bool

@router.patch("/users/{user_id}/status")
async def update_user_status(
    user_id: str,
    payload: UserStatusUpdate,
    token_data: dict = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db)
):
    """Admin only: Suspend or Reactivate a user account."""
    if token_data.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can manage users")
        
    from app.repositories.user_repository import user_repository
    user = await user_repository.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Prevent self-suspension
    if str(user.id) == token_data.get("sub"):
        raise HTTPException(status_code=400, detail="Cannot suspend your own account")
        
    await user_repository.update(db, db_obj=user, obj_in={"is_active": payload.is_active})
    
    # If suspended, force logout via websocket
    if not payload.is_active:
        from app.services.websocket_manager import manager
        await manager.broadcast_to_case("global", {
            "type": "force_logout",
            "user_id": str(user.id)
        })
        
    status_msg = "reactivated" if payload.is_active else "suspended"
    return success_response(message=f"User account {status_msg} successfully")

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
        select(func.count(User.id)).where(User.role.has(name="client"))
    )
    total_clients = clients_result.scalar() or 0
    
    # 2. Total Advocates
    advocates_result = await db.execute(
        select(func.count(User.id)).where(User.role.has(name="advocate"))
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
                "joined_at": user.created_at.isoformat() if user.created_at else None,
                "is_active": user.is_active
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

from pydantic import BaseModel
from uuid import UUID

class CaseStatusOverride(BaseModel):
    status: CaseStatus

@router.patch("/cases/{case_id}/status")
async def override_case_status(
    case_id: UUID,
    data: CaseStatusOverride,
    token_data: dict = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Forcefully override a case's status.
    """
    if token_data.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can override case status"
        )
        
    stmt = select(Case).where(Case.id == case_id)
    result = await db.execute(stmt)
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )
        
    old_status = case.status
    case.status = data.status
    
    # Log the action
    audit_log = AuditLog(
        user_id=UUID(token_data.get("sub")),
        action="UPDATE_CASE",
        resource_type="case",
        resource_id=str(case.id),
        old_values={"status": old_status.value},
        new_values={"status": case.status.value},
        ip_address="admin-override"
    )
    db.add(audit_log)
    
    await db.commit()
    
    return success_response(
        data={"status": case.status.value},
        message=f"Case status successfully overridden to {case.status.value}"
    )

@router.delete("/cases/{case_id}")
async def delete_case(
    case_id: UUID,
    token_data: dict = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Forcefully delete a case and archive it from the system.
    """
    if token_data.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete cases"
        )
        
    stmt = select(Case).where(Case.id == case_id)
    result = await db.execute(stmt)
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )
        
    # We must manually delete payments first because Payment -> Case is ondelete="RESTRICT"
    # to protect financial ledgers, but Admin deletion forces cleanup.
    await db.execute(Payment.__table__.delete().where(Payment.case_id == case_id))
        
    # We will log the deletion before actually deleting it
    audit_log = AuditLog(
        user_id=UUID(token_data.get("sub")),
        action="DELETE_CASE",
        resource_type="case",
        resource_id=str(case.id),
        old_values={"case_number": case.case_number, "status": case.status.value},
        new_values=None,
        ip_address="admin-delete"
    )
    db.add(audit_log)
    
    await db.delete(case)
    
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
    return success_response(
        data={"deleted_id": str(case_id)},
        message="Case permanently deleted"
    )
