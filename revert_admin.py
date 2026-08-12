import asyncio
from app.database.session import _get_session_factory
from sqlalchemy import select
from app.models.user import User
from app.models.role import Role

async def main():
    factory = _get_session_factory()
    async with factory() as db:
        role_query = select(Role).where(Role.name == "advocate")
        result = await db.execute(role_query)
        advocate_role = result.scalars().first()

        email = "amitesh.mangoit@yopmail.com"
        user_query = select(User).where(User.email == email)
        result = await db.execute(user_query)
        user = result.scalars().first()
        
        if user and advocate_role:
            user.role_id = advocate_role.id
            await db.commit()
            print(f"Success! {email} reverted to advocate.")

asyncio.run(main())
