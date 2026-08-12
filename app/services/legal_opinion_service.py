from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from app.models.legal_opinion import LegalOpinion, OpinionStatus
from app.models.case import Case, CaseStatus
from app.models.advocate import Advocate
from app.repositories.legal_opinion_repository import legal_opinion_repository
from app.api.v1.cases.schemas import LegalOpinionRequest
from sqlalchemy import select

class LegalOpinionService:
    @staticmethod
    async def get_opinion_by_case(db: AsyncSession, case_id: str) -> LegalOpinion:
        return await legal_opinion_repository.get_by_case_id(db, case_id)
        
    @staticmethod
    async def create_or_update_opinion(db: AsyncSession, user_id: str, case_id: str, data: LegalOpinionRequest) -> LegalOpinion:
        # 1. Fetch case directly using SQLAlchemy
        case_query = select(Case).where(Case.id == case_id)
        result = await db.execute(case_query)
        case = result.scalars().first()
        
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
            
        # 2. Get advocate ID from user_id (Optional for admins/testing)
        advocate_query = select(Advocate).where(Advocate.user_id == user_id)
        result = await db.execute(advocate_query)
        advocate = result.scalars().first()
        
        # We will not raise an exception if not found, to allow admins to test this
        advocate_id = str(advocate.id) if advocate else None

        # 3. Check if opinion exists
        opinion = await legal_opinion_repository.get_by_case_id(db, case_id)
        
        if opinion:
            # Update existing
            update_data = data.dict(exclude_unset=True)
            if data.status == OpinionStatus.FINALIZED or data.status == "finalized":
                update_data["status"] = OpinionStatus.FINALIZED
            opinion = await legal_opinion_repository.update(db, db_obj=opinion, obj_in=update_data)
        else:
            # Create new
            create_data = data.dict()
            create_data["case_id"] = case_id
            create_data["advocate_id"] = advocate_id
            if data.status == OpinionStatus.FINALIZED or data.status == "finalized":
                create_data["status"] = OpinionStatus.FINALIZED
            opinion = await legal_opinion_repository.create(db, create_data)
            
        # 4. Update case status if finalized
        if data.status == OpinionStatus.FINALIZED or data.status == "finalized":
            case.status = CaseStatus.OPINION_GENERATED
            db.add(case)
            
        await db.commit()
        return opinion

legal_opinion_service = LegalOpinionService()
