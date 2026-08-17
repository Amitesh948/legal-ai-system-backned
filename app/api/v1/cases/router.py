from typing import List

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.common.responses import success_response
from app.core.security import get_current_user_token
from app.database.session import get_db
from app.api.v1.cases.schemas import CaseCreateRequest, CaseResponse, CaseDocumentResponse
from app.services.case_service import case_service
from app.services.ai_service import ai_service

router = APIRouter()

@router.post("/", response_model=dict, status_code=201)
async def create_case(
    data: CaseCreateRequest,
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(get_current_user_token)
):
    """Create a new case for the logged in client."""
    user_id = token_data.get("sub")
    if token_data.get("role") != "client":
        raise HTTPException(status_code=403, detail="Only clients can create cases")
        
    case = await case_service.create_case(db, user_id, data)
    return success_response(message="Case created successfully", data={"id": str(case.id)})

@router.get("/", response_model=dict)
async def get_my_cases(
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(get_current_user_token)
):
    """Get all cases for the logged in user (role-aware)."""
    user_id = token_data.get("sub")
    role = token_data.get("role")
    
    if role == "advocate":
        cases = await case_service.get_advocate_cases(db, user_id)
    elif role == "admin":
        cases = await case_service.get_all_cases(db)
    else:
        cases = await case_service.get_client_cases(db, user_id)
    
    # Serialize the cases properly to avoid SQLAlchemy DetachedInstanceError
    serialized_cases = []
    for c in cases:
        serialized_cases.append({
            "id": str(c.id),
            "title": c.title,
            "description": c.description,
            "status": c.status.value if hasattr(c.status, 'value') else c.status,
            "priority": c.priority.value if hasattr(c.priority, 'value') else c.priority,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "documents": [
                {
                    "id": str(d.id),
                    "file_name": d.original_name,
                    "mime_type": d.mime_type
                } for d in c.documents
            ]
        })
        
    return success_response(message="Cases retrieved", data=serialized_cases)

@router.get("/admin/analytics", response_model=dict)
async def get_admin_analytics(
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(get_current_user_token)
):
    """Get analytics data for admin dashboard."""
    role = token_data.get("role")
    if role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    from sqlalchemy import select, func
    from app.models.case import Case, CaseStatus
    from app.models.payment import Payment, PaymentStatus
    
    # Revenue Overview (Last 6 Months logic could be added, but for MVP let's just get total by month or just total)
    # Simple totals for MVP:
    total_revenue_query = select(func.sum(Payment.amount)).where(Payment.status == PaymentStatus.SUCCESS)
    rev_result = await db.execute(total_revenue_query)
    total_revenue = rev_result.scalar() or 0
    
    # Case Status Breakdown
    status_query = select(Case.status, func.count(Case.id)).group_by(Case.status)
    status_result = await db.execute(status_query)
    status_counts = {row[0].value if hasattr(row[0], 'value') else row[0]: row[1] for row in status_result.all()}
    
    # Top Rated Advocates
    # Join Advocate User profile with Case client_rating
    from app.models.user import User
    from app.models.role import Role
    advocates_query = (
        select(
            User.first_name, 
            User.last_name, 
            func.avg(Case.client_rating).label('avg_rating'),
            func.count(Case.id).label('total_cases')
        )
        .join(Case, User.id == Case.advocate_id)
        .where(Case.client_rating.isnot(None))
        .group_by(User.id)
        .order_by(func.avg(Case.client_rating).desc())
        .limit(5)
    )
    adv_results = await db.execute(advocates_query)
    top_advocates = [
        {
            "name": f"{r[0]} {r[1]}",
            "rating": round(float(r[2]), 1),
            "cases": r[3]
        }
        for r in adv_results.all()
    ]
    
    data = {
        "revenue": {
            "total": total_revenue
        },
        "case_status": status_counts,
        "top_advocates": top_advocates
    }
    
    return success_response(message="Analytics retrieved", data=data)

@router.get("/admin/all", response_model=dict)
async def get_all_cases_admin(
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(get_current_user_token)
):
    """Admin only: Get all cases across all clients."""
    if token_data.get("role") not in ["admin", "advocate"]:
        raise HTTPException(status_code=403, detail="Only admins can view all cases")
        
    cases = await case_service.get_all_cases(db)
    
    serialized_cases = []
    for c in cases:
        # Return advocate's user_id (not profile id) so frontend dropdown matches
        adv_user_id = None
        if c.advocate:
            adv_user_id = str(c.advocate.user_id)
            
        serialized_cases.append({
            "id": str(c.id),
            "title": c.title,
            "status": c.status.value if hasattr(c.status, 'value') else c.status,
            "client_id": str(c.client_id),
            "advocate_id": adv_user_id,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })
        
    return success_response(message="All cases retrieved", data=serialized_cases)

@router.get("/admin/advocates", response_model=dict)
async def get_all_advocates(
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(get_current_user_token)
):
    """Admin only: Get a list of all advocates to assign cases to."""
    if token_data.get("role") not in ["admin", "advocate"]:
        raise HTTPException(status_code=403, detail="Only admins can view advocates list")
        
    from sqlalchemy import select
    from app.models.user import User
    
    # Simple query to get all users with 'advocate' role
    # Assuming role is managed dynamically, let's just query by role_id or join with roles
    # Since we don't have the role name easily available here without join, let's just join roles
    from app.models.role import Role
    query = select(User).join(Role, User.role_id == Role.id).where(Role.name == "advocate")
    result = await db.execute(query)
    advocates = result.scalars().all()
    
    data = [{"user_id": str(a.id), "name": f"{a.first_name} {a.last_name}", "email": a.email} for a in advocates]
    return success_response(message="Advocates retrieved", data=data)

@router.post("/{case_id}/assign", response_model=dict)
async def assign_case_to_advocate(
    case_id: str,
    data: dict, # Expected {"advocate_user_id": "uuid..."}
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(get_current_user_token)
):
    """Admin only: Assign a case to an advocate."""
    if token_data.get("role") not in ["admin", "advocate"]:
        raise HTTPException(status_code=403, detail="Only admins can assign cases")
        
    advocate_user_id = data.get("advocate_user_id")
    if not advocate_user_id:
        raise HTTPException(status_code=400, detail="advocate_user_id is required")
        
    case = await case_service.assign_case(db, case_id, advocate_user_id)
    return success_response(message="Case assigned successfully", data={"case_id": str(case.id)})

@router.get("/{case_id}", response_model=dict)
async def get_case(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(get_current_user_token)
):
    """Get a specific case's details."""
    user_id = token_data.get("sub")
    role = token_data.get("role", "client")
    c = await case_service.get_case_by_id(db, user_id, case_id, role)
    
    # Also fetch AI Summary if it exists
    ai_summary_data = None
    if getattr(c, 'ai_summary', None):
        ai_summary_data = {
            "summary_text": c.ai_summary.summary,
            "important_facts": c.ai_summary.important_facts,
            "timeline": c.ai_summary.timeline,
            "legal_issues": c.ai_summary.legal_issues,
            "suggested_sections": c.ai_summary.suggested_sections,
            "suggested_actions": c.ai_summary.suggested_actions,
            "status": c.ai_summary.status.value if hasattr(c.ai_summary.status, 'value') else c.ai_summary.status
        }
    
    serialized_case = {
        "id": str(c.id),
        "case_number": c.case_number,
        "title": c.title,
        "description": c.description,
        "status": c.status.value if hasattr(c.status, 'value') else c.status,
        "priority": c.priority.value if hasattr(c.priority, 'value') else c.priority,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "ai_summary": ai_summary_data,
        "documents": [
            {
                "id": str(d.id),
                "file_name": d.original_name,
                "mime_type": d.mime_type,
                "file_size": d.file_size
            } for d in c.documents
        ]
    }
    return success_response(message="Case retrieved", data=serialized_case)

@router.get("/{case_id}/documents/{doc_id}/download")
async def download_document(
    case_id: str,
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(get_current_user_token)
):
    """Download a specific document."""
    import os
    from sqlalchemy import select
    from app.models.case_document import CaseDocument
    
    query = select(CaseDocument).where(CaseDocument.id == doc_id, CaseDocument.case_id == case_id)
    result = await db.execute(query)
    doc = result.scalars().first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        path=doc.file_path,
        filename=doc.original_name,
        media_type=doc.mime_type
    )

@router.post("/{case_id}/documents", response_model=dict)
async def upload_case_document(
    case_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(get_current_user_token)
):
    """Upload a document for a specific case."""
    user_id = token_data.get("sub")
    doc = await case_service.upload_document(db, case_id, user_id, file)
    from app.models.case import Case, CaseStatus
    from sqlalchemy import select
    
    query = select(Case).where(Case.id == case_id)
    result = await db.execute(query)
    case = result.scalars().first()
    
    # Only trigger AI processing for the initial document upload
    if case and case.status == CaseStatus.NEW:
        background_tasks.add_task(
            ai_service.process_document_background,
            case_id=case_id,
            document_id=str(doc.id),
            file_path=doc.file_path
        )
    
    return success_response(message="Document uploaded successfully", data={"document_id": str(doc.id)})

@router.post("/{case_id}/document-chat", response_model=dict)
async def chat_with_document(
    case_id: str,
    data: dict,
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(get_current_user_token)
):
    """Q&A with the uploaded document."""
    question = data.get("question")
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")
        
    from sqlalchemy import select
    from app.models.case_document import CaseDocument
    
    # Get the latest document for this case
    query = select(CaseDocument).where(CaseDocument.case_id == case_id).order_by(CaseDocument.created_at.desc())
    result = await db.execute(query)
    doc = result.scalars().first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="No document found for this case")
        
    import os
    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="Document file not found on disk")
        
    from app.services.ai_service import ai_service
    text = ai_service.extract_text(doc.file_path)
    
    answer = await ai_service.ask_document_question(text, question)
    
    return success_response(message="Answer generated", data={"answer": answer})

@router.get("/{case_id}/opinion", response_model=dict)
async def get_legal_opinion(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(get_current_user_token)
):
    """Get the legal opinion for a specific case."""
    from app.services.legal_opinion_service import legal_opinion_service
    opinion = await legal_opinion_service.get_opinion_by_case(db, case_id)
    if not opinion:
        return success_response(message="No opinion found", data=None)
        
    data = {
        "id": str(opinion.id),
        "legal_opinion": opinion.legal_opinion,
        "winning_probability": opinion.winning_probability,
        "risk_assessment": opinion.risk_assessment,
        "recommended_actions": opinion.recommended_actions,
        "ai_summary_edited": opinion.ai_summary_edited,
        "status": opinion.status.value if hasattr(opinion.status, 'value') else opinion.status,
    }
    return success_response(message="Legal opinion retrieved", data=data)

@router.post("/{case_id}/opinion", response_model=dict)
async def create_or_update_legal_opinion(
    case_id: str,
    data: dict, # Using dict directly to bypass Pydantic model import issues for now
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(get_current_user_token)
):
    """Create or update a legal opinion for a case."""
    user_id = token_data.get("sub")
    if token_data.get("role") not in ["advocate", "admin"]:
        raise HTTPException(status_code=403, detail="Only advocates can provide legal opinions")
        
    from app.services.legal_opinion_service import legal_opinion_service
    from app.api.v1.cases.schemas import LegalOpinionRequest
    
    opinion_req = LegalOpinionRequest(**data)
    opinion = await legal_opinion_service.create_or_update_opinion(db, user_id, case_id, opinion_req)
    
    return success_response(message="Legal opinion saved successfully", data={"id": str(opinion.id)})

@router.post("/{case_id}/report/generate", response_model=dict)
async def generate_legal_report(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(get_current_user_token)
):
    """Generate the final PDF report for the case."""
    user_id = token_data.get("sub")
    role = token_data.get("role")
    
    if role not in ["admin", "advocate"]:
        raise HTTPException(status_code=403, detail="Only admins or advocates can generate reports")
        
    from app.services.report_service import report_service
    from app.models.report import Report, ReportStatus
    from sqlalchemy import select
    import os
    
    # 1. Generate the PDF
    try:
        file_path = await report_service.generate_legal_opinion_report(db, case_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    # 2. Save or update Report metadata in DB
    report_query = select(Report).where(Report.case_id == case_id)
    result = await db.execute(report_query)
    existing_report = result.scalars().first()
    
    file_name = os.path.basename(file_path)
    
    if existing_report:
        existing_report.file_path = file_path
        existing_report.file_name = file_name
        existing_report.status = ReportStatus.COMPLETED
        db.add(existing_report)
    else:
        new_report = Report(
            case_id=case_id,
            generated_by=user_id,
            file_path=file_path,
            file_name=file_name,
            status=ReportStatus.COMPLETED
        )
        db.add(new_report)
        
    await db.commit()
    
    # 3. Trigger Notifications
    from app.models.case import Case
    from app.models.client import Client
    from app.models.user import User
    from app.models.notification import Notification
    from app.services.email_service import email_service
    from app.services.notification_helper import should_send_email
    import asyncio
    
    case_query = select(Case).where(Case.id == case_id)
    case_result = await db.execute(case_query)
    case = case_result.scalars().first()
    
    if case:
        user_query = select(User).join(Client, Client.user_id == User.id).where(Client.id == case.client_id)
        user_result = await db.execute(user_query)
        client_user = user_result.scalars().first()
        
        if client_user:
            case_num = case.case_number if hasattr(case, 'case_number') else str(case.id)[:8]
            
            # In-app notification
            db.add(Notification(
                user_id=client_user.id,
                title="Legal Report Ready",
                message=f"The final legal opinion report for case {case_num} has been generated and is ready to download.",
                type="report",
                metadata_info={"link": f"/cases/{case.id}"}
            ))
            await db.commit()
            
            # Email notification
            email_allowed = await should_send_email(db, str(client_user.id))
            if email_allowed:
                asyncio.create_task(
                    email_service.send_final_report_email(
                        to_email=client_user.email,
                        name=f"{client_user.first_name} {client_user.last_name}",
                        case_number=case_num,
                        pdf_path=file_path
                    )
                )
    
    return success_response(message="Report generated and emailed successfully", data={"file_name": file_name})

@router.get("/{case_id}/report/download")
async def download_legal_report(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(get_current_user_token)
):
    """Download the finalized PDF report."""
    from app.models.report import Report
    from sqlalchemy import select
    import os
    from fastapi.responses import FileResponse
    
    report_query = select(Report).where(Report.case_id == case_id)
    result = await db.execute(report_query)
    report = result.scalars().first()
    
    if not report or not report.file_path:
        raise HTTPException(status_code=404, detail="Report not generated yet")
        
    if not os.path.exists(report.file_path):
        raise HTTPException(status_code=404, detail="Report file not found on disk")
        
    from app.models.audit_log import AuditLog
    user_id = token_data.get("sub")
    db.add(AuditLog(
        user_id=user_id,
        action="REPORT_DOWNLOAD",
        resource_type="report",
        resource_id=report.id,
        new_values={"details": f"Downloaded report {report.file_name} for case {case_id}"}
    ))
    await db.commit()
        
    return FileResponse(
        path=report.file_path,
        filename=report.file_name,
        media_type="application/pdf"
    )

@router.post("/{case_id}/close", response_model=dict)
async def close_case(
    case_id: str,
    data: dict,
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(get_current_user_token)
):
    """Close the case and save client rating and feedback."""
    from app.models.case import Case, CaseStatus
    from sqlalchemy import select
    
    user_id = token_data.get("sub")
    role = token_data.get("role")
    
    if role != "client":
        raise HTTPException(status_code=403, detail="Only the client can close the case and provide a rating")
        
    query = select(Case).where(Case.id == case_id)
    result = await db.execute(query)
    case = result.scalars().first()
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    # We allow closing if report is generated or opinion is generated
    if case.status not in [CaseStatus.REPORT_GENERATED, CaseStatus.OPINION_GENERATED, CaseStatus.COMPLETED]:
        raise HTTPException(status_code=400, detail="Case cannot be closed yet.")
        
    rating = data.get("rating")
    review = data.get("review")
    
    case.client_rating = rating
    case.client_review = review
    case.status = CaseStatus.COMPLETED
    
    await db.commit()
    
    return success_response(message="Case closed successfully. Thank you for your feedback!")


@router.get("/{case_id}/messages", response_model=dict)
async def get_case_messages(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(get_current_user_token)
):
    """Get all chat messages for a specific case."""
    from app.models.case_message import CaseMessage
    from app.models.user import User
    from app.models.case import Case
    from app.models.role import Role
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    
    # Check permissions
    role = token_data.get("role")
    user_id = token_data.get("sub")
    
    if role != "admin":
        # Validate that the user is actually part of this case
        await case_service.get_case_by_id(db, user_id, case_id, role)

    query = (
        select(CaseMessage)
        .options(selectinload(CaseMessage.sender).selectinload(User.role))
        .where(CaseMessage.case_id == case_id)
        .order_by(CaseMessage.created_at.asc())
    )
    result = await db.execute(query)
    messages = result.scalars().all()

    response_data = []
    for msg in messages:
        sender_name = f"{msg.sender.first_name} {msg.sender.last_name}" if msg.sender else "Unknown"
        sender_role = msg.sender.role.name if msg.sender and msg.sender.role else "unknown"
        response_data.append({
            "id": str(msg.id),
            "case_id": str(msg.case_id),
            "sender_id": str(msg.sender_id),
            "message_text": msg.message_text,
            "is_read": msg.is_read,
            "created_at": msg.created_at.isoformat(),
            "sender_name": sender_name,
            "sender_role": sender_role
        })

    return success_response(message="Messages retrieved successfully", data=response_data)

@router.post("/{case_id}/messages", response_model=dict)
async def send_case_message(
    case_id: str,
    data: dict,
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(get_current_user_token)
):
    """Send a chat message for a specific case."""
    from app.models.case_message import CaseMessage
    from app.api.v1.cases.schemas import CaseMessageRequest
    
    user_id = token_data.get("sub")
    req = CaseMessageRequest(**data)
    
    new_message = CaseMessage(
        case_id=case_id,
        sender_id=user_id,
        message_text=req.message_text
    )
    db.add(new_message)
    await db.commit()
    await db.refresh(new_message)
    
    # Ideally, trigger an email notification here if recipient is offline!
    
    # Broadcast message via WebSocket
    from app.services.websocket_manager import manager
    from app.models.user import User
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select
    
    # We need sender name and role for the broadcast payload
    query = select(User).options(selectinload(User.role)).where(User.id == user_id)
    result = await db.execute(query)
    sender = result.scalars().first()
    
    sender_name = f"{sender.first_name} {sender.last_name}" if sender else "Unknown"
    sender_role = sender.role.name if sender and sender.role else "unknown"
    
    ws_payload = {
        "id": str(new_message.id),
        "case_id": str(new_message.case_id),
        "sender_id": str(new_message.sender_id),
        "message_text": new_message.message_text,
        "is_read": new_message.is_read,
        "created_at": new_message.created_at.isoformat(),
        "sender_name": sender_name,
        "sender_role": sender_role
    }
    await manager.broadcast_to_case(case_id, {"type": "new_message", "data": ws_payload})
    
    return success_response(message="Message sent successfully", data={"id": str(new_message.id)})

from fastapi import WebSocket, WebSocketDisconnect

@router.websocket("/ws/{case_id}")
async def websocket_endpoint(websocket: WebSocket, case_id: str):
    from app.services.websocket_manager import manager
    await manager.connect(websocket, case_id)
    try:
        while True:
            data = await websocket.receive_text()
            # If we want to handle typing events:
            import json
            try:
                event = json.loads(data)
                if event.get("type") == "typing":
                    # Broadcast typing status to everyone else in this case
                    await manager.broadcast_to_case(case_id, {
                        "type": "typing",
                        "sender_id": event.get("sender_id")
                    })
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket, case_id)
