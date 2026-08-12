import asyncio
from app.database.session import _get_session_factory
from app.services.auth_service import auth_service
from app.api.v1.auth.schemas import RegisterRequest

async def main():
    factory = _get_session_factory()
    async with factory() as db:
        req = RegisterRequest(
            email="amitesh.mangoit@yopmail.com",
            first_name="John",
            last_name="Snow",
            password="Any!23456",
            role="advocate",
            verification_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhbWl0ZXNoLm1hbmdvaXRAeW9wbWFpbC5jb20iLCJ0eXBlIjoidmVyaWZpY2F0aW9uIiwiZXhwIjoxNzg2MDA4NTc1fQ.j2IsKmZqOkkXhJpaKOuhPvq2xI0inxp9X6ph5Smkn9I"
        )
        try:
            res = await auth_service.register_user(db, req)
            print("Success:", res)
        except Exception as e:
            import traceback
            traceback.print_exc()

asyncio.run(main())
