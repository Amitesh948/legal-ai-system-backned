"""
Legal AI System - CMS Models
==============================
Models for dynamic website content (Settings, Home, FAQs, Practice Areas, etc.).
"""

from sqlalchemy import Column, String, Text, Boolean, Integer, JSON
from app.models.base import BaseModel

class WebsiteSettings(BaseModel):
    """Global settings for the website (Contact info, social links, etc.)"""
    __tablename__ = "website_settings"

    # Only one row should theoretically exist, but we can have 'active'
    is_active = Column(Boolean, default=True)
    
    # Contact Information
    address = Column(Text, nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    office_hours = Column(String(255), nullable=True)
    
    # Social Links (stored as JSON, e.g., {"facebook": "url", "linkedin": "url"})
    social_links = Column(JSON, nullable=True, default=dict)
    
    # Footer Config
    footer_text = Column(Text, nullable=True)
    copyright_text = Column(String(255), nullable=True)


class HeroSection(BaseModel):
    """Homepage Hero section dynamic content"""
    __tablename__ = "hero_sections"
    
    title = Column(String(255), nullable=False)
    subtitle = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    primary_cta_text = Column(String(50), nullable=True, default="Get Started")
    primary_cta_link = Column(String(255), nullable=True, default="/register")
    secondary_cta_text = Column(String(50), nullable=True, default="Learn More")
    secondary_cta_link = Column(String(255), nullable=True, default="/about")
    is_active = Column(Boolean, default=True)


class PracticeArea(BaseModel):
    """Dynamic Practice Areas (e.g., Corporate Law, Family Law)"""
    __tablename__ = "practice_areas"
    
    title = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True)
    short_description = Column(String(500), nullable=True)
    detailed_content = Column(Text, nullable=True)
    icon_name = Column(String(50), nullable=True, default="gavel") # Material icon name
    image_url = Column(String(500), nullable=True)
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)


class FAQ(BaseModel):
    """Frequently Asked Questions"""
    __tablename__ = "faqs"
    
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    category = Column(String(100), nullable=True, default="General")
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)


class PageContent(BaseModel):
    """Generic pages like About Us, Terms & Conditions"""
    __tablename__ = "page_contents"
    
    title = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True) # 'about-us', 'terms', 'privacy'
    content = Column(Text, nullable=False)
    seo_title = Column(String(255), nullable=True)
    seo_description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

class Blog(BaseModel):
    """Dynamic Blog Posts"""
    __tablename__ = "blogs"
    
    title = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True)
    content = Column(Text, nullable=False)
    author_name = Column(String(255), nullable=True)
    category = Column(String(100), nullable=True)
    featured_image_url = Column(String(500), nullable=True)
    is_published = Column(Boolean, default=False)
    seo_title = Column(String(255), nullable=True)
    seo_description = Column(Text, nullable=True)
