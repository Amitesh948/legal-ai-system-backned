import asyncio
from app.database.session import get_db
from app.services.case_service import case_service

async def main():
    async for db in get_db():
        cases = await case_service.get_client_cases(db, "1306bd74-ddbb-4740-9ebf-4f5dd69768a3") # dummy uuid
        print(cases)

asyncio.run(main())
