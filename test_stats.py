import asyncio
from sqlalchemy import select, func
from app.database.session import get_db, _get_session_factory
from app.models.user import User
from app.models.case import Case, CaseStatus
from app.models.payment import Payment, PaymentStatus

async def main():
    session_factory = _get_session_factory()
    async with session_factory() as db:
        try:
            print("Fetching clients...")
            clients_result = await db.execute(select(func.count(User.id)).where(User.role.has(name="client")))
            total_clients = clients_result.scalar() or 0
            
            print("Fetching advocates...")
            advocates_result = await db.execute(select(func.count(User.id)).where(User.role.has(name="advocate")))
            total_advocates = advocates_result.scalar() or 0
            
            print("Fetching active cases...")
            active_cases_result = await db.execute(select(func.count(Case.id)).where(Case.status.not_in([CaseStatus.COMPLETED, CaseStatus.CANCELLED])))
            total_active_cases = active_cases_result.scalar() or 0
            
            print("Fetching revenue...")
            revenue_result = await db.execute(select(func.sum(Payment.amount)).where(Payment.status == PaymentStatus.SUCCESS))
            total_revenue = float(revenue_result.scalar() or 0)
            print(f"Stats: {total_clients}, {total_advocates}, {total_active_cases}, {total_revenue}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
