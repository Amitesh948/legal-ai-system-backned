from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.legal_opinion import LegalOpinion
from app.repositories.base import BaseRepository

class LegalOpinionRepository(BaseRepository[LegalOpinion]):
    async def get_by_case_id(self, db: AsyncSession, case_id: str) -> Optional[LegalOpinion]:
        query = select(self.model).where(self.model.case_id == case_id)
        result = await db.execute(query)
        return result.scalars().first()

legal_opinion_repository = LegalOpinionRepository(LegalOpinion)
