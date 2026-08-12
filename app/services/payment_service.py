import razorpay
import hmac
import hashlib
from datetime import datetime, timezone
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

import logging

from app.config import get_settings
from app.models.payment import Payment, PaymentStatus
from sqlalchemy import select
from app.repositories.payment_repository import payment_repo

logger = logging.getLogger(__name__)
settings = get_settings()

class PaymentService:
    def __init__(self):
        if settings.razorpay_key_id and settings.razorpay_key_secret:
            self.client = razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))
        else:
            self.client = None

    async def create_payment_order(self, db: AsyncSession, case_id: UUID, user_id: UUID, user_role: str, amount: float, currency: str = "INR") -> Payment:
        """
        Creates a Razorpay order and saves a PENDING Payment record in DB.
        """
        if not self.client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Razorpay is not configured on the server."
            )

        # 1. Verify case belongs to client
        from app.models.case import Case
        from app.models.client import Client
        result = await db.execute(select(Case).where(Case.id == case_id))
        case = result.scalars().first()
        
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
            
        client_result = await db.execute(select(Client).where(Client.id == case.client_id))
        client = client_result.scalars().first()
        
        if user_role == "client":
            if not client or str(client.user_id) != str(user_id):
                raise HTTPException(status_code=403, detail="Not authorized to pay for this case")

        # 2. Create Razorpay order
        amount_in_paise = int(amount * 100)
        
        try:
            order_data = {
                "amount": amount_in_paise,
                "currency": currency,
                "receipt": str(case_id),
                "notes": {
                    "case_id": str(case_id),
                    "client_id": str(client.id) if client else ""
                }
            }
            
            # MOCK MODE: If the user hasn't configured real Razorpay keys in .env
            import os
            from app.config import get_settings
            settings = get_settings()
            
            if settings.razorpay_key_secret == "your-razorpay-key-secret" or not settings.razorpay_key_secret:
                import time
                # Generate a mock order ID
                rzp_order = {"id": f"mock_order_{int(time.time())}"}
                logger.warning(f"RAZORPAY MOCK MODE: Generated mock order {rzp_order['id']} because .env keys are missing.")
            else:
                # Real Razorpay API Call
                rzp_order = self.client.order.create(data=order_data)
                
        except Exception as e:
            logger.error(f"Razorpay order creation failed: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to create Razorpay order: {str(e)}")

        payment_data = {
            "case_id": case_id,
            "client_id": client.id,
            "amount": amount,
            "currency": currency,
            "razorpay_order_id": rzp_order["id"],
            "status": PaymentStatus.PENDING
        }
        
        payment = await payment_repo.create(db, payment_data)
        
        # If an advocate creates the order, update the case status to PAYMENT_PENDING
        if user_role == "advocate":
            from app.models.case import CaseStatus
            case.status = CaseStatus.PAYMENT_PENDING
            await db.commit()
            
        return payment

    async def verify_payment(self, db: AsyncSession, razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str) -> Payment:
        """
        Verifies the Razorpay signature and marks the payment as SUCCESS.
        """
        if not self.client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Razorpay is not configured on the server."
            )

        # 1. Verify signature with Razorpay SDK (or manually)
        if razorpay_order_id.startswith("mock_order_"):
            logger.warning(f"RAZORPAY MOCK MODE: Bypassing signature verification for {razorpay_order_id}")
        else:
            try:
                params_dict = {
                    'razorpay_order_id': razorpay_order_id,
                    'razorpay_payment_id': razorpay_payment_id,
                    'razorpay_signature': razorpay_signature
                }
                self.client.utility.verify_payment_signature(params_dict)
            except razorpay.errors.SignatureVerificationError:
                raise HTTPException(status_code=400, detail="Invalid payment signature")
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Payment verification failed: {str(e)}")

        # 2. Update Payment Record
        payment = await payment_repo.get_by_razorpay_order_id(db, razorpay_order_id)
        if not payment:
            raise HTTPException(status_code=404, detail="Payment record not found")
        
        if payment.status == PaymentStatus.SUCCESS:
            return payment # Already verified

        update_data = {
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature,
            "status": PaymentStatus.SUCCESS,
            "paid_at": datetime.now(timezone.utc)
        }
        
        updated_payment = await payment_repo.update(db, db_obj=payment, obj_in=update_data)
        
        # 3. Update Case Status
        from app.models.case import Case, CaseStatus
        result = await db.execute(select(Case).where(Case.id == payment.case_id))
        case = result.scalars().first()
        
        if case:
            case.status = CaseStatus.PAYMENT_COMPLETED
            await db.commit()
            await db.refresh(case)
            
            # Audit log for payment
            from app.models.audit_log import AuditLog
            from app.models.client import Client
            from app.models.user import User
            user_result = await db.execute(
                select(User).join(Client, Client.user_id == User.id).where(Client.id == case.client_id)
            )
            user = user_result.scalars().first()
            if user:
                db.add(AuditLog(
                    user_id=user.id,
                    action="PAYMENT_COMPLETED",
                    resource_type="payment",
                    resource_id=payment.id,
                    new_values={"details": f"Payment of {payment.amount} successful for case {case.id}"}
                ))
                await db.commit()
            
            # 4. Trigger Notifications
            from app.services.email_service import email_service
            from app.services.notification_helper import should_send_email
            from app.models.notification import Notification
            
            # We need the user's email and name. We have the client object.
            # However, client_id is the Client model. We need to fetch the User to get email/name.
            from app.models.client import Client
            from app.models.user import User
            user_result = await db.execute(
                select(User).join(Client, Client.user_id == User.id).where(Client.id == case.client_id)
            )
            user = user_result.scalars().first()
            if user:
                # In-app notification (always create)
                case_num = case.case_number if hasattr(case, 'case_number') else str(case.id)[:8]
                db.add(Notification(
                    user_id=user.id,
                    title="Payment Received",
                    message=f"Payment of ₹{float(payment.amount)} for case {case_num} was successful.",
                    type="payment",
                    metadata_info={"link": f"/cases/{case.id}"}
                ))
                await db.commit()
                
                # Email notification
                email_allowed = await should_send_email(db, str(user.id))
                if email_allowed:
                    import asyncio
                    # Use asyncio.create_task to run it in the background without blocking the API
                    asyncio.create_task(
                        email_service.send_payment_receipt(
                            to_email=user.email,
                            name=f"{user.first_name} {user.last_name}",
                            case_number=case_num,
                            amount=float(payment.amount)
                        )
                    )
            
        return updated_payment

    async def handle_webhook(self, db: AsyncSession, payload_body: str, signature: str) -> None:
        """
        Handles Razorpay webhooks (e.g. payment.captured, refund.processed)
        """
        if not settings.razorpay_webhook_secret:
            logger.warning("Webhook received but razorpay_webhook_secret is not configured")
            raise HTTPException(status_code=400, detail="Webhook not configured")

        try:
            self.client.utility.verify_webhook_signature(
                payload_body, 
                signature, 
                settings.razorpay_webhook_secret
            )
        except razorpay.errors.SignatureVerificationError:
            raise HTTPException(status_code=400, detail="Invalid webhook signature")
            
        import json
        payload = json.loads(payload_body)
        event = payload.get("event")
        
        if event == "payment.captured":
            payment_entity = payload["payload"]["payment"]["entity"]
            order_id = payment_entity.get("order_id")
            payment_id = payment_entity.get("id")
            
            if order_id:
                payment = await payment_repo.get_by_razorpay_order_id(db, order_id)
                if payment and payment.status != PaymentStatus.SUCCESS:
                    update_data = {
                        "razorpay_payment_id": payment_id,
                        "status": PaymentStatus.SUCCESS,
                        "paid_at": datetime.now(timezone.utc)
                    }
                    await payment_repo.update(db, payment, update_data)
                    
                    from app.models.case import Case
                    result = await db.execute(select(Case).where(Case.id == payment.case_id))
                    case = result.scalars().first()
                    
                    if case and case.status.value in ["payment_pending", "new"]:
                        case.status = "payment_completed"
                        await db.commit()
                        await db.refresh(case)
        
        elif event == "refund.processed":
            payment_entity = payload["payload"]["refund"]["entity"]
            payment_id = payment_entity.get("payment_id")
            # Implement refund logic here by finding the payment by razorpay_payment_id
            pass

payment_service = PaymentService()
