from typing import Optional, List, Dict, Any
from sqlalchemy import select, or_, String, cast
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import JSONB

from app.models.citation import Citation
from app.repositories.base import BaseRepository

class CitationRepository(BaseRepository[Citation]):
    def __init__(self):
        super().__init__(Citation)

    async def search(self, db: AsyncSession, query: str = "", category: str = "", skip: int = 0, limit: int = 100) -> List[Citation]:
        stmt = select(self.model)
        
        conditions = []
        if query:
            search_term = f"%{query}%"
            conditions.append(
                or_(
                    self.model.title.ilike(search_term),
                    self.model.act_name.ilike(search_term),
                    self.model.section_number.ilike(search_term),
                    self.model.case_reference.ilike(search_term),
                    cast(self.model.keywords, String).ilike(search_term)
                )
            )
            
        if category:
            conditions.append(self.model.category.ilike(category))
            
        if conditions:
            stmt = stmt.where(*conditions)
            
        stmt = stmt.order_by(self.model.created_at.desc()).offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        return list(result.scalars().all())

citation_repository = CitationRepository()
