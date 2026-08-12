import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.case import Case, CaseStatus
from app.models.user import User
from app.models.client import Client
from app.models.advocate import Advocate
from app.models.legal_opinion import LegalOpinion
from app.config import get_settings

settings = get_settings()

class ReportService:
    def __init__(self):
        # Configure Jinja2 environment
        self.templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
        self.env = Environment(loader=FileSystemLoader(self.templates_dir))
        
        # Directory to store generated reports
        self.reports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "media", "reports")
        os.makedirs(self.reports_dir, exist_ok=True)

    async def generate_legal_opinion_report(self, db: AsyncSession, case_id: str) -> str:
        """
        Fetches case, opinion, and user details to generate a PDF report.
        Returns the absolute path to the generated PDF.
        """
        # 1. Fetch Case with relationships
        case_query = (
            select(Case)
            .options(
                selectinload(Case.legal_opinion),
                selectinload(Case.ai_summary),
                selectinload(Case.client).selectinload(Client.user),
                selectinload(Case.advocate).selectinload(Advocate.user)
            )
            .where(Case.id == case_id)
        )
        result = await db.execute(case_query)
        case = result.scalars().first()

        if not case:
            raise ValueError("Case not found")
        if not case.legal_opinion:
            raise ValueError("No finalized legal opinion found for this case")

        # 2. Extract Data for Template
        client_name = f"{case.client.user.first_name} {case.client.user.last_name}" if case.client and case.client.user else "Unknown Client"
        advocate_name = f"{case.advocate.user.first_name} {case.advocate.user.last_name}" if case.advocate and case.advocate.user else "Unknown Advocate"
        
        # Replace newlines with <br> for HTML rendering of text areas
        legal_opinion_text = case.legal_opinion.legal_opinion.replace('\n', '<br>') if case.legal_opinion.legal_opinion else ""
        risk_assessment_text = case.legal_opinion.risk_assessment.replace('\n', '<br>') if case.legal_opinion.risk_assessment else ""
        recommended_actions_text = case.legal_opinion.recommended_actions.replace('\n', '<br>') if case.legal_opinion.recommended_actions else ""
        
        ai_summary_text = None
        if case.legal_opinion.ai_summary_edited:
            ai_summary_text = case.legal_opinion.ai_summary_edited.replace('\n', '<br>')
        elif case.ai_summary:
            ai_summary_text = case.ai_summary.summary_text.replace('\n', '<br>')

        case_status_str = case.status.value if hasattr(case.status, 'value') else str(case.status)

        template_data = {
            "case_number": case.case_number,
            "client_name": client_name,
            "date_generated": datetime.now().strftime("%B %d, %Y"),
            "advocate_name": advocate_name,
            "case_status": case_status_str.replace("_", " ").title(),
            "winning_probability": case.legal_opinion.winning_probability or "N/A",
            "case_title": case.title,
            "case_description": case.description or "No description provided.",
            "legal_opinion": legal_opinion_text,
            "risk_assessment": risk_assessment_text,
            "recommended_actions": recommended_actions_text,
            "ai_summary": ai_summary_text,
            "watermark_text": settings.report_watermark_text
        }

        # 3. Render HTML
        template = self.env.get_template("legal_report.html")
        html_out = template.render(template_data)

        # 4. Generate PDF
        file_name = f"Legal_Opinion_Report_{case.case_number}_{int(datetime.now().timestamp())}.pdf"
        file_path = os.path.join(self.reports_dir, file_name)
        
        HTML(string=html_out).write_pdf(file_path)
        
        # 5. Update case status (Optional, maybe router does this)
        if case_status_str != CaseStatus.COMPLETED.value:
            case.status = CaseStatus.REPORT_GENERATED
            db.add(case)
            await db.commit()

        return file_path

report_service = ReportService()
