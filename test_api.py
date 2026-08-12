import asyncio
from sqlalchemy import select
from app.database.session import _get_session_factory
from app.models.case import Case
from app.services.case_service import case_service

async def main():
    factory = _get_session_factory()
    async with factory() as db:
        case = (await db.execute(select(Case).order_by(Case.created_at.desc()))).scalars().first()
        if not case:
            print("No case found")
            return
        client = await case.awaitable_attrs.client
        c = await case_service.get_case_by_id(db, client.user_id, str(case.id))
        
        print(f"Has AI Summary? {hasattr(c, 'ai_summary') and c.ai_summary is not None}")
        if c.ai_summary:
            print(f"Summary Text: {c.ai_summary.summary}")

asyncio.run(main())
