from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.citation import Citation
from app.repositories.citation_repository import citation_repository
from app.api.v1.citations.schemas import CitationCreate, CitationUpdate

class CitationService:
    async def create_citation(
        self, db: AsyncSession, advocate_id: str, data: CitationCreate
    ) -> Citation:
        # First find advocate ID from user_id if token subject is user_id
        from app.models.advocate import Advocate
        adv_query = select(Advocate).where(Advocate.user_id == advocate_id)
        result = await db.execute(adv_query)
        advocate = result.scalars().first()
        
        real_adv_id = str(advocate.id) if advocate else None
        
        create_data = data.model_dump()
        create_data["added_by"] = real_adv_id
        
        citation = await citation_repository.create(db, obj_in=create_data)
        return citation
        
    async def get_citation(self, db: AsyncSession, citation_id: str) -> Citation:
        citation = await citation_repository.get(db, id=citation_id)
        if not citation:
            raise ValueError("Citation not found")
        return citation
        
    async def update_citation(
        self, db: AsyncSession, citation_id: str, data: CitationUpdate
    ) -> Citation:
        citation = await citation_repository.get(db, id=citation_id)
        if not citation:
            raise ValueError("Citation not found")
            
        update_data = data.model_dump(exclude_unset=True)
        updated_citation = await citation_repository.update(db, db_obj=citation, obj_in=update_data)
        return updated_citation
        
    async def delete_citation(self, db: AsyncSession, citation_id: str) -> bool:
        citation = await citation_repository.get(db, id=citation_id)
        if not citation:
            raise ValueError("Citation not found")
            
        await citation_repository.delete(db, id=citation_id)
        return True
        
    async def search_citations(
        self, db: AsyncSession, query: str = "", category: str = "", skip: int = 0, limit: int = 100
    ) -> List[Citation]:
        return await citation_repository.search(db, query=query, category=category, skip=skip, limit=limit)

citation_service = CitationService()
