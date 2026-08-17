"""
Legal AI System - Admin CMS Router
====================================
Endpoints for Admins to manage dynamic website content.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from app.database.session import get_db
from app.api.common.responses import success_response
from app.core.security import get_current_user_token
from app.models.cms import WebsiteSettings, HeroSection, PracticeArea, FAQ, PageContent

router = APIRouter()

def require_admin(token_data: dict = Depends(get_current_user_token)):
    if token_data.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can manage CMS content")
    return token_data

# --- Website Settings ---
class SettingsUpdate(BaseModel):
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    office_hours: Optional[str] = None
    social_links: Optional[dict] = None
    footer_text: Optional[str] = None
    copyright_text: Optional[str] = None

@router.put("/settings")
async def update_settings(
    payload: SettingsUpdate,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_admin)
):
    result = await db.execute(select(WebsiteSettings).where(WebsiteSettings.is_active == True))
    settings = result.scalars().first()
    
    if not settings:
        settings = WebsiteSettings()
        db.add(settings)
        
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(settings, key, value)
        
    await db.commit()
    return success_response(message="Settings updated successfully")

# --- FAQs ---
class FAQCreate(BaseModel):
    question: str
    answer: str
    category: str = "General"
    display_order: int = 0
    is_active: bool = True

@router.get("/faqs")
async def admin_get_faqs(db: AsyncSession = Depends(get_db), _ = Depends(require_admin)):
    result = await db.execute(select(FAQ).order_by(FAQ.display_order))
    return success_response(data=[{
        "id": str(f.id),
        "question": f.question,
        "answer": f.answer,
        "category": f.category,
        "display_order": f.display_order,
        "is_active": f.is_active
    } for f in result.scalars().all()])

@router.post("/faqs")
async def create_faq(payload: FAQCreate, db: AsyncSession = Depends(get_db), _ = Depends(require_admin)):
    faq = FAQ(**payload.model_dump())
    db.add(faq)
    await db.commit()
    return success_response(message="FAQ created successfully")

@router.put("/faqs/{id}")
async def update_faq(id: str, payload: FAQCreate, db: AsyncSession = Depends(get_db), _ = Depends(require_admin)):
    result = await db.execute(select(FAQ).where(FAQ.id == id))
    faq = result.scalars().first()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")
        
    for key, value in payload.model_dump().items():
        setattr(faq, key, value)
        
    await db.commit()
    return success_response(message="FAQ updated successfully")

@router.delete("/faqs/{id}")
async def delete_faq(id: str, db: AsyncSession = Depends(get_db), _ = Depends(require_admin)):
    result = await db.execute(select(FAQ).where(FAQ.id == id))
    faq = result.scalars().first()
    if faq:
        await db.delete(faq)
        await db.commit()
    return success_response(message="FAQ deleted successfully")

# --- Pages ---
class PageCreate(BaseModel):
    title: str
    slug: str
    content: str
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    is_active: bool = True

@router.get("/pages")
async def admin_get_pages(db: AsyncSession = Depends(get_db), _ = Depends(require_admin)):
    result = await db.execute(select(PageContent))
    return success_response(data=[{
        "id": str(p.id),
        "title": p.title,
        "slug": p.slug,
        "seo_title": p.seo_title,
        "is_active": p.is_active
    } for p in result.scalars().all()])

@router.post("/pages")
async def create_page(payload: PageCreate, db: AsyncSession = Depends(get_db), _ = Depends(require_admin)):
    page = PageContent(**payload.model_dump())
    db.add(page)
    await db.commit()
    return success_response(message="Page created successfully")

@router.put("/pages/{id}")
async def update_page(id: str, payload: PageCreate, db: AsyncSession = Depends(get_db), _ = Depends(require_admin)):
    result = await db.execute(select(PageContent).where(PageContent.id == id))
    page = result.scalars().first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
        
    for key, value in payload.model_dump().items():
        setattr(page, key, value)
        
    await db.commit()
    return success_response(message="Page updated successfully")

@router.get("/pages/{id}")
async def admin_get_page_detail(id: str, db: AsyncSession = Depends(get_db), _ = Depends(require_admin)):
    result = await db.execute(select(PageContent).where(PageContent.id == id))
    page = result.scalars().first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return success_response(data={
        "id": str(page.id),
        "title": page.title,
        "slug": page.slug,
        "content": page.content,
        "seo_title": page.seo_title,
        "seo_description": page.seo_description,
        "is_active": page.is_active
    })
