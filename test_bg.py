import asyncio
from app.services.ai_service import ai_service
async def main():
    res = await ai_service.generate_summary("This is a test legal document about a contract.")
    print(res)
asyncio.run(main())
