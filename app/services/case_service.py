"""
Legal AI System - Case Service
================================
Business logic for Case Management and Document Uploads.
"""
import os
import shutil
from typing import List
from uuid import uuid4

from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.case import Case
from app.models.case_document import CaseDocument
from app.models.client import Client
from app.config import get_settings

settings = get_settings()

class CaseService:
    @staticmethod
    async def create_case(db: AsyncSession, user_id: str, data: dict) -> Case:
        # Auto-create Client profile if it doesn't exist (since we skipped onboarding)
        client_query = select(Client).where(Client.user_id == user_id)
        result = await db.execute(client_query)
        client = result.scalars().first()
        
        if not client:
            client = Client(user_id=user_id)
            db.add(client)
            await db.commit()
            await db.refresh(client)

        new_case = Case(
            case_number=f"CASE-{str(uuid4())[:8].upper()}",
            title=data.title,
            description=data.description,
            priority=data.priority,
            client_id=client.id,
            status="NEW"
        )
        db.add(new_case)
        await db.commit()
        await db.refresh(new_case)
        return new_case

    @staticmethod
    async def get_client_cases(db: AsyncSession, user_id: str) -> List[Case]:
        query = (
            select(Case)
            .join(Client, Case.client_id == Client.id)
            .options(selectinload(Case.documents))
            .where(Client.user_id == user_id)
            .order_by(Case.created_at.desc())
        )
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_advocate_cases(db: AsyncSession, user_id: str) -> List[Case]:
        """Get all cases assigned to a specific advocate by their user_id."""
        from app.models.advocate import Advocate
        query = (
            select(Case)
            .join(Advocate, Case.advocate_id == Advocate.id)
            .options(selectinload(Case.documents))
            .where(Advocate.user_id == user_id)
            .order_by(Case.created_at.desc())
        )
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_all_cases(db: AsyncSession) -> List[Case]:
        """Admin only: Get all cases in the system"""
        query = (
            select(Case)
            .options(
                selectinload(Case.documents),
                selectinload(Case.advocate)
            )
            .order_by(Case.created_at.desc())
        )
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def assign_case(db: AsyncSession, case_id: str, advocate_id: str) -> Case:
        """Admin only: Assign a case to an advocate by advocate user_id"""
        from app.models.advocate import Advocate
        from sqlalchemy import select
        
        # Look up the actual advocate record ID from the provided user_id
        advocate_query = select(Advocate).where(Advocate.user_id == advocate_id)
        result = await db.execute(advocate_query)
        advocate = result.scalars().first()
        
        # If no advocate profile exists yet (for testing), create one
        if not advocate:
            advocate = Advocate(user_id=advocate_id)
            db.add(advocate)
            await db.commit()
            await db.refresh(advocate)
            
        case_query = select(Case).where(Case.id == case_id)
        case_res = await db.execute(case_query)
        case = case_res.scalars().first()
        
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
            
        case.advocate_id = advocate.id
        await db.commit()
        await db.refresh(case)
        return case

    @staticmethod
    async def get_case_by_id(db: AsyncSession, user_id: str, case_id: str, role: str = "client") -> Case:
        from app.models.advocate import Advocate
        
        base_options = [
            selectinload(Case.documents),
            selectinload(Case.ai_summary)
        ]
        
        if role == "admin":
            # Admin can view any case
            query = (
                select(Case)
                .options(*base_options)
                .where(Case.id == case_id)
            )
        elif role == "advocate":
            # Advocate can view cases assigned to them
            query = (
                select(Case)
                .join(Advocate, Case.advocate_id == Advocate.id)
                .options(*base_options)
                .where(Advocate.user_id == user_id, Case.id == case_id)
            )
        else:
            # Client can view their own cases
            query = (
                select(Case)
                .join(Client, Case.client_id == Client.id)
                .options(*base_options)
                .where(Client.user_id == user_id, Case.id == case_id)
            )
            
        result = await db.execute(query)
        case = result.scalars().first()
        if not case:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Case not found")
        return case

    @staticmethod
    async def upload_document(db: AsyncSession, case_id: str, user_id: str, file: UploadFile) -> CaseDocument:
        import hashlib
        # Validate extension
        _, ext = os.path.splitext(file.filename)
        if ext.lower() not in settings.allowed_extensions_list:
            raise HTTPException(status_code=400, detail="File type not allowed")

        # Ensure upload directory exists
        os.makedirs(settings.upload_dir, exist_ok=True)

        # Create unique filename
        unique_filename = f"{uuid4()}{ext}"
        file_path = os.path.join(settings.upload_dir, unique_filename)

        # Save to disk and calculate hash
        file_hash_obj = hashlib.sha256()
        try:
            with open(file_path, "wb") as buffer:
                while True:
                    chunk = file.file.read(8192)
                    if not chunk:
                        break
                    buffer.write(chunk)
                    file_hash_obj.update(chunk)
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to save file")

        # Save to DB
        doc = CaseDocument(
            case_id=case_id,
            uploaded_by=user_id,
            file_name=unique_filename,
            original_name=file.filename,
            file_path=file_path,
            mime_type=file.content_type or "application/octet-stream",
            file_size=os.path.getsize(file_path),
            file_hash=file_hash_obj.hexdigest()
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
        return doc

case_service = CaseService()
