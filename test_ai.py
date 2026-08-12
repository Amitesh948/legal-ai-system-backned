import asyncio
from sqlalchemy import select
from app.database.session import _get_session_factory
from app.models.ai_summary import AISummary

async def main():
    factory = _get_session_factory()
    async with factory() as db:
        result = await db.execute(select(AISummary).order_by(AISummary.created_at.desc()))
        summaries = result.scalars().all()
        print(f"Total summaries: {len(summaries)}")
        for s in summaries:
            print(f"ID: {s.id}")
            print(f"Summary: {s.summary_text}")
            print(f"Key Issues: {s.key_issues}")
            print("-----------------------")

asyncio.run(main())
