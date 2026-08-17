import asyncio
from sqlalchemy import select
from app.database.session import get_db, SessionLocal
from app.models.cms import WebsiteSettings

async def main():
    async with SessionLocal() as db:
        result = await db.execute(select(WebsiteSettings).where(WebsiteSettings.is_active == True))
        settings = result.scalars().first()
        if not settings:
            print("Settings not found, creating new.")
            settings = WebsiteSettings()
            db.add(settings)
        
        settings.address = "16 mangoitsolutions"
        settings.email = "amitesh.mangoit@gmail.com"
        settings.office_hours = "9:30 to 7:15"
        settings.phone = "1234554321"
        try:
            await db.commit()
            print("Successfully updated settings")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
