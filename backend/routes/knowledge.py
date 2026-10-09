from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.routes.shipments import get_current_company
from backend.services.knowledge_ingestion_service import (
    KnowledgeIngestionService,
)


router = APIRouter(
    prefix="/api/knowledge",
    tags=["knowledge"],
)


@router.post("/upload")
async def upload_knowledge_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload a company-private knowledge document for RAG.

    Supported formats:
    - Markdown (.md)
    - Plain text (.txt)
    """

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="A filename is required.",
        )

    filename = file.filename.lower()

    if not filename.endswith((".md", ".txt")):
        raise HTTPException(
            status_code=400,
            detail="Only Markdown and TXT knowledge documents are supported.",
        )

    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="The uploaded knowledge document is empty.",
        )

    company = get_current_company(db)

    service = KnowledgeIngestionService()

    try:
        chunks_ingested = service.ingest_company_document(
            company_id=company.id,
            filename=file.filename,
            content=file_bytes,
        )
    except (UnicodeDecodeError, ValueError) as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return {
        "filename": file.filename,
        "chunks_ingested": chunks_ingested,
        "company_id": company.id,
    }