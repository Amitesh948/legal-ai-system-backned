import asyncio
from uuid import UUID
from app.database.session import _get_session_factory
from app.models.payment import Payment, PaymentStatus

async def test():
    session_factory = _get_session_factory()
    async with session_factory() as db:
        try:
            payment = Payment(
                case_id=UUID("9200ecf9-60d2-4bf5-800a-51112b423f8f"),
                client_id=UUID("0ec7686b-04f4-4a1f-be08-6bbed5da0204"),
                amount=4999,
                currency="INR",
                razorpay_order_id="test_rzp_123",
                status=PaymentStatus.PENDING
            )
            db.add(payment)
            await db.commit()
            print("SUCCESS")
        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test())
