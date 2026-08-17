import asyncio
from sqlalchemy import select
from app.database.session import async_session
from app.models.case import Case
from app.models.payment import Payment

async def test():
    async with async_session() as db:
        q = select(Case.status)
        r = await db.execute(q)
        print("Cases:", r.all())
asyncio.run(test())
