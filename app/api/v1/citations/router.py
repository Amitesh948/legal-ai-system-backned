from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.common.responses import success_response
from app.core.security import get_current_user_token
from app.database.session import get_db
from app.services.citation_service import citation_service
from app.api.v1.citations.schemas import CitationCreate, CitationUpdate, CitationResponse

router = APIRouter(tags=["Citations"])

@router.post("", response_model=dict)
async def create_citation(
    data: CitationCreate,
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(get_current_user_token)
):
    if token_data.get("role") not in ["admin", "advocate"]:
        raise HTTPException(status_code=403, detail="Not authorized to create citations")
        
    citation = await citation_service.create_citation(db, token_data.get("sub"), data)
    return success_response(message="Citation created successfully", data={"id": str(citation.id)})

@router.get("/search", response_model=dict)
async def search_citations(
    q: str = Query("", description="Search term for title, keywords, etc."),
    category: str = Query("", description="Filter by category"),
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(get_current_user_token)
):
    if token_data.get("role") not in ["admin", "advocate"]:
        raise HTTPException(status_code=403, detail="Not authorized to search citations")
        
    citations = await citation_service.search_citations(db, q, category, skip, limit)
    # Map to dict since Response schema might conflict with nested models sometimes if not configured well
    return success_response(
        message="Citations retrieved successfully",
        data=[CitationResponse.model_validate(c).model_dump() for c in citations]
    )

@router.get("/{citation_id}", response_model=dict)
async def get_citation(
    citation_id: str,
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(get_current_user_token)
):
    if token_data.get("role") not in ["admin", "advocate"]:
        raise HTTPException(status_code=403, detail="Not authorized to view citations")
        
    try:
        citation = await citation_service.get_citation(db, citation_id)
        return success_response(
            message="Citation retrieved successfully",
            data=CitationResponse.model_validate(citation).model_dump()
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{citation_id}", response_model=dict)
async def update_citation(
    citation_id: str,
    data: CitationUpdate,
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(get_current_user_token)
):
    if token_data.get("role") not in ["admin", "advocate"]:
        raise HTTPException(status_code=403, detail="Not authorized to update citations")
        
    try:
        citation = await citation_service.update_citation(db, citation_id, data)
        return success_response(message="Citation updated successfully", data={"id": str(citation.id)})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{citation_id}", response_model=dict)
async def delete_citation(
    citation_id: str,
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(get_current_user_token)
):
    if token_data.get("role") not in ["admin", "advocate"]:
        raise HTTPException(status_code=403, detail="Not authorized to delete citations")
        
    try:
        await citation_service.delete_citation(db, citation_id)
        return success_response(message="Citation deleted successfully", data={"id": citation_id})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
