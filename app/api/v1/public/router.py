"""
Legal AI System - Public CMS Router
====================================
Read-only endpoints for the main public-facing website.
No authentication is required for these endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.session import get_db
from app.api.common.responses import success_response
from app.models.cms import WebsiteSettings, HeroSection, PracticeArea, FAQ, PageContent, Blog
from app.models.advocate import Advocate
from app.models.user import User

router = APIRouter()

@router.get("/settings")
async def get_public_settings(db: AsyncSession = Depends(get_db)):
    """Get global website settings like address, phone, footer, social links."""
    result = await db.execute(select(WebsiteSettings).where(WebsiteSettings.is_active == True))
    settings = result.scalars().first()
    
    if not settings:
        return success_response(data={
            "address": "", "phone": "", "email": "", "social_links": {}, "footer_text": "", "copyright_text": "© 2026 Legal AI System"
        })
        
    return success_response(data={
        "address": settings.address,
        "phone": settings.phone,
        "email": settings.email,
        "office_hours": settings.office_hours,
        "social_links": settings.social_links,
        "footer_text": settings.footer_text,
        "copyright_text": settings.copyright_text
    })

@router.get("/home")
async def get_public_home(db: AsyncSession = Depends(get_db)):
    """Get the homepage configuration (Hero, Featured Practice Areas, etc.)"""
    # Get active hero section
    hero_res = await db.execute(select(HeroSection).where(HeroSection.is_active == True))
    hero = hero_res.scalars().first()
    
    # Get top 4 practice areas
    pa_res = await db.execute(select(PracticeArea).where(PracticeArea.is_active == True).order_by(PracticeArea.display_order).limit(4))
    practice_areas = pa_res.scalars().all()
    
    # Get top 3 FAQs
    faq_res = await db.execute(select(FAQ).where(FAQ.is_active == True).order_by(FAQ.display_order).limit(3))
    faqs = faq_res.scalars().all()

    return success_response(data={
        "hero": {
            "title": hero.title if hero else "Modern Legal Solutions",
            "subtitle": hero.subtitle if hero else "Expert AI-powered legal assistance.",
            "image_url": hero.image_url if hero else "",
            "primary_cta_text": hero.primary_cta_text if hero else "Get Started",
            "primary_cta_link": hero.primary_cta_link if hero else "/register",
            "secondary_cta_text": hero.secondary_cta_text if hero else "Learn More",
            "secondary_cta_link": hero.secondary_cta_link if hero else "/about"
        },
        "practice_areas": [{"title": p.title, "slug": p.slug, "short_description": p.short_description, "icon_name": p.icon_name} for p in practice_areas],
        "faqs": [{"question": f.question, "answer": f.answer} for f in faqs]
    })

@router.get("/practice-areas")
async def get_practice_areas(db: AsyncSession = Depends(get_db)):
    """Get all active practice areas."""
    result = await db.execute(select(PracticeArea).where(PracticeArea.is_active == True).order_by(PracticeArea.display_order))
    return success_response(data=[{
        "title": p.title,
        "slug": p.slug,
        "short_description": p.short_description,
        "detailed_content": p.detailed_content,
        "icon_name": p.icon_name,
        "image_url": p.image_url
    } for p in result.scalars().all()])

@router.get("/faqs")
async def get_faqs(db: AsyncSession = Depends(get_db)):
    """Get all active FAQs."""
    result = await db.execute(select(FAQ).where(FAQ.is_active == True).order_by(FAQ.display_order))
    return success_response(data=[{
        "question": f.question,
        "answer": f.answer,
        "category": f.category
    } for f in result.scalars().all()])

@router.get("/pages/{slug}")
async def get_page(slug: str, db: AsyncSession = Depends(get_db)):
    """Get dynamic page content (e.g., about-us, terms, privacy)."""
    result = await db.execute(select(PageContent).where(PageContent.slug == slug, PageContent.is_active == True))
    page = result.scalars().first()
    
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
        
    return success_response(data={
        "title": page.title,
        "content": page.content,
        "seo_title": page.seo_title,
        "seo_description": page.seo_description
    })

@router.get("/attorneys")
async def get_attorneys(db: AsyncSession = Depends(get_db)):
    """Get all approved and available advocates for public display."""
    query = (
        select(Advocate, User)
        .join(User, Advocate.user_id == User.id)
        .where(Advocate.verification_status == "approved", User.is_active == True)
    )
    result = await db.execute(query)
    
    attorneys = []
    for adv, user in result.all():
        attorneys.append({
            "id": str(adv.id),
            "name": f"{user.first_name} {user.last_name}",
            "district": adv.district,
            "state": adv.state,
            "practice_areas": adv.practice_areas,
            "experience": adv.experience_years,
            "education": adv.llb_degree
        })
        
    return success_response(data=attorneys)
