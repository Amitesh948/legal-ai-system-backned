import os
import json
import asyncio
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.case import Case, CaseStatus
from app.models.ai_summary import AISummary, AISummaryStatus
from app.config import get_settings
from app.services.ocr import ocr_manager

settings = get_settings()
logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        # We will initialize this only when needed, in case the key isn't loaded right away.
        self.client_initialized = False

    def extract_text(self, file_path: str) -> str:
        """
        Extract text from any document type using the OCR Manager.
        
        Supports: PDF (native + scanned), DOCX, JPG, PNG.
        - Native PDFs → pdfplumber (fast)
        - Scanned PDFs → pdfplumber detects no text → auto-OCR via EasyOCR
        - Images (JPG/PNG) → direct OCR via EasyOCR
        - DOCX → python-docx
        """
        logger.info(f"Extracting text from: {file_path}")
        text = ocr_manager.extract_text(file_path)
        logger.info(f"Extracted {len(text)} characters from {os.path.basename(file_path)}")
        return text

    async def generate_summary(self, text: str) -> dict:
        """Use Gemini REST API directly to bypass Python 3.8 SDK limitations."""
        import httpx
        from app.config import get_settings
        
        settings = get_settings()
        api_key = settings.openai_api_key
        if not api_key:
            return {"summary": "API Key missing.", "key_risks": [], "deadlines": "None"}
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={api_key}"
        
        prompt = f"""
        Act as a Senior Legal Advocate. Analyze the following legal document text and provide a comprehensive structured summary.
        You MUST respond in valid JSON format with exactly these keys:
        - "summary": A brief, plain-English summary of what this document is.
        - "important_facts": A list of strings, extracting key factual points.
        - "timeline": A list of objects with 'date' and 'event' string keys.
        - "legal_issues": A list of strings identifying core legal problems.
        - "suggested_legal_sections": A list of strings (e.g., "IPC 420", "CrPC 156").
        - "suggested_actions": A list of strings for next steps (e.g., "File FIR").

        Document Text:
        {text[:10000]}
        """
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=30.0)
                data = response.json()
                
                # Extract text from Gemini response
                if "candidates" in data and len(data["candidates"]) > 0:
                    response_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    
                    # Clean markdown formatting if present
                    if response_text.startswith('```json'):
                        response_text = response_text[7:-3]
                    elif response_text.startswith('```'):
                        response_text = response_text[3:-3]
                        
                    return json.loads(response_text)
                else:
                    print(f"Gemini API returned unexpectedly: {data}")
                    return {
                        "summary": "AI generation failed or text too complex.", 
                        "important_facts": [], 
                        "timeline": [],
                        "legal_issues": [],
                        "suggested_legal_sections": [],
                        "suggested_actions": []
                    }
        except Exception as e:
            print(f"AI Generation Error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "summary": "AI generation failed. Fallback triggered.",
                "important_facts": [], 
                "timeline": [],
                "legal_issues": [],
                "suggested_legal_sections": [],
                "suggested_actions": []
            }

    async def ask_document_question(self, text: str, question: str) -> str:
        """Query the Gemini model directly about the document text."""
        import httpx
        api_key = settings.openai_api_key  # We are using Gemini API key stored here
        if not api_key:
            return "AI feature is disabled (API key missing)."
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={api_key}"
        
        prompt = f"""
        You are a highly capable legal assistant. Answer the user's question based strictly on the provided legal document text.
        If the answer is not contained in the text, simply state that you cannot find the answer in the provided document.
        Be concise, accurate, and professional.

        Document Text:
        {text[:10000]}

        Question:
        {question}
        """
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=30.0)
                data = response.json()
                
                if "candidates" in data and len(data["candidates"]) > 0:
                    return data["candidates"][0]["content"]["parts"][0]["text"].strip()
                else:
                    return "Sorry, I could not generate an answer at this time."
        except Exception as e:
            print(f"Document Q&A Error: {e}")
            return "An error occurred while connecting to the AI service."

    async def process_document_background(self, case_id: str, document_id: str, file_path: str):
        """Background task to extract text, summarize, and update DB."""
        # Need a new DB session since we are in a background task
        from app.database.session import _get_session_factory
        session_factory = _get_session_factory()
        
        async with session_factory() as db:
            try:
                # 1. Update Case Status to AI Processing
                query = select(Case).where(Case.id == case_id)
                result = await db.execute(query)
                case = result.scalars().first()
                if case:
                    case.status = CaseStatus.AI_PROCESSING
                    await db.commit()

                # 2. Extract Text
                text = self.extract_text(file_path)
                
                # 3. Generate Summary
                if not text.strip():
                    ai_result = {
                        "summary": "No readable text found in document.",
                        "important_facts": [], 
                        "timeline": [],
                        "legal_issues": [],
                        "suggested_legal_sections": [],
                        "suggested_actions": ["Upload a readable PDF."]
                    }
                else:
                    ai_result = await self.generate_summary(text)

                # 4. Save Summary to DB
                import datetime
                
                # Make sure to import timezone
                from datetime import timezone
                
                summary = AISummary(
                    case_id=case_id,
                    summary=ai_result.get("summary", ""),
                    important_facts=ai_result.get("important_facts", []),
                    timeline=ai_result.get("timeline", []),
                    legal_issues=ai_result.get("legal_issues", []),
                    suggested_sections=ai_result.get("suggested_legal_sections", []),
                    suggested_actions=ai_result.get("suggested_actions", []),
                    status=AISummaryStatus.COMPLETED,
                    processed_at=datetime.datetime.now(timezone.utc),
                    model_used="gemini-3.5-flash"
                )
                db.add(summary)
                
                # 5. Update Case Status to UNDER_REVIEW
                if case:
                    case.status = CaseStatus.UNDER_REVIEW
                    
                await db.commit()
                
                # 6. Trigger Notifications
                if case:
                    from app.models.client import Client
                    from app.models.user import User
                    from app.models.notification import Notification
                    from app.services.notification_helper import should_send_email
                    user_result = await db.execute(
                        select(User).join(Client, Client.user_id == User.id).where(Client.id == case.client_id)
                    )
                    user = user_result.scalars().first()
                    if user:
                        # In-app notification
                        case_num = case.case_number if hasattr(case, 'case_number') else str(case.id)[:8]
                        db.add(Notification(
                            user_id=user.id,
                            title="AI Summary Ready",
                            message=f"The AI summary for case {case_num} is complete. Your case is now under review by an advocate.",
                            type="case_status",
                            metadata_info={"link": f"/cases/{case.id}"}
                        ))
                        await db.commit()
                        
                        # Email notification
                        email_allowed = await should_send_email(db, str(user.id))
                        if email_allowed:
                            from app.services.email_service import email_service
                            import asyncio
                            asyncio.create_task(
                                email_service.send_case_status_update(
                                    to_email=user.email,
                                    name=f"{user.first_name} {user.last_name}",
                                    case_number=case_num,
                                    new_status="UNDER_REVIEW"
                                )
                            )
            except Exception as e:
                import traceback
                print(f"Background task failed: {e}")
                print(traceback.format_exc())
                # Rollback and set error status if possible
                await db.rollback()

ai_service = AIService()
