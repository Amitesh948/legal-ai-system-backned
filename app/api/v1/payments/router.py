import logging
from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user_token
from app.database.session import get_db
from app.api.v1.payments import schemas
from app.api.common.responses import success_response
from app.services.payment_service import payment_service
from app.repositories.payment_repository import payment_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["payments"])

@router.post("/order", response_model=dict)
async def create_order(
    data: schemas.PaymentCreate,
    token_data: dict = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Creates a Razorpay order for a specific case and returns the razorpay_order_id.
    """
    user_id_str = token_data.get("sub")
    user_role = token_data.get("role")
    
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = UUID(user_id_str)
    
    payment = await payment_service.create_payment_order(
        db=db,
        case_id=data.case_id,
        user_id=user_id,
        user_role=user_role,
        amount=data.amount,
        currency=data.currency
    )
    
    # Return formatted for frontend consumption
    response_data = schemas.PaymentOrderResponse.model_validate(payment).model_dump()
    return success_response(data=response_data, message="Order created successfully")

@router.post("/verify", response_model=dict)
async def verify_payment(
    data: schemas.PaymentVerify,
    token_data: dict = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Verifies the Razorpay payment signature and marks the payment as successful.
    """
    try:
        payment = await payment_service.verify_payment(
            db=db,
            razorpay_order_id=data.razorpay_order_id,
            razorpay_payment_id=data.razorpay_payment_id,
            razorpay_signature=data.razorpay_signature
        )
        
        response_data = schemas.PaymentResponse.model_validate(payment).model_dump()
        return success_response(data=response_data, message="Payment verified successfully")
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        return {"success": False, "message": f"ERROR TRACEBACK: {tb}", "data": None}

@router.get("/case/{case_id}", response_model=dict)
async def get_case_payments(
    case_id: UUID,
    token_data: dict = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all payments associated with a specific case.
    """
    payments = await payment_repo.get_by_case_id(db, case_id)
    response_data = [schemas.PaymentResponse.model_validate(p).model_dump() for p in payments]
    return success_response(data=response_data)

@router.get("/my-payments", response_model=dict)
async def get_my_payments(
    token_data: dict = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all payments made by the current authenticated client, with case details.
    """
    from app.models.client import Client
    from app.models.case import Case
    from sqlalchemy import select
    
    user_id = UUID(token_data.get("sub"))
    
    # Get client id for this user
    client_result = await db.execute(select(Client).where(Client.user_id == user_id))
    client = client_result.scalars().first()
    
    if not client:
        return success_response(data=[], message="No payments found")
        
    payments = await payment_repo.get_by_client_id(db, client.id)
    
    history_data = []
    for p in payments:
        case_result = await db.execute(select(Case).where(Case.id == p.case_id))
        case = case_result.scalars().first()
        case_number = case.case_number if case and hasattr(case, 'case_number') else str(p.case_id)[:8]
        
        history_data.append({
            "id": str(p.id),
            "amount": float(p.amount),
            "status": p.status,
            "razorpay_order_id": p.razorpay_order_id,
            "razorpay_payment_id": p.razorpay_payment_id,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "case_id": str(p.case_id),
            "case_number": case_number
        })
        
    return success_response(data=history_data)

@router.post("/webhook", response_model=dict)
async def razorpay_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Razorpay Webhook endpoint for async payment status updates.
    """
    payload = await request.body()
    signature = request.headers.get("x-razorpay-signature")
    
    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")
        
    await payment_service.handle_webhook(db, payload.decode("utf-8"), signature)
    
    return {"status": "ok"}
