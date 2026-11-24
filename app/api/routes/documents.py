import os
import gc 
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.config import settings
from app.database.db import get_db
from app.database.models import DocumentModel
from app.api.schemas import (
    DocumentResponse,
    DocumentQueryRequest,
    DocumentQueryResponse,
)
from app.services.document_service import document_service
from app.rag.retriever import rag_retriever
from app.utils.logger import logger

router = APIRouter(prefix="/api/documents", tags=["Documents & RAG"])

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".csv", ".txt"}
MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB limit


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    safe_filename = os.path.basename(file.filename or "")
    if not safe_filename:
        raise HTTPException(status_code=400, detail="Invalid filename provided.")

    ext = Path(safe_filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    content = await file.read()
    file_size = len(content)
    if file_size == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File size exceeds the 15 MB maximum limit.")

    destination_path = settings.uploads_dir / safe_filename
    try:
        with open(destination_path, "wb") as f:
            f.write(content)
            del content
            gc.collect()

        # Process and index document into ChromaDB vector store
        indexed = document_service.process_file(str(destination_path), safe_filename)
        if not indexed:
            logger.warning(f"Document saved at {destination_path}, but text indexing returned False.")

        doc_record = DocumentModel(
            filename=safe_filename,
            file_path=str(destination_path),
            file_type=ext.lstrip("."),
            file_size=file_size,
        )
        db.add(doc_record)
        db.commit()
        db.refresh(doc_record)
        logger.info(f"Uploaded and registered document #{doc_record.id}: {safe_filename}")
        return doc_record
    except Exception as e:
        db.rollback()
        logger.error(f"Document upload failed for {safe_filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process uploaded file: {str(e)}")


@router.get("/", response_model=List[DocumentResponse])
def list_uploaded_documents(db: Session = Depends(get_db)):
    return db.query(DocumentModel).order_by(DocumentModel.uploaded_at.desc()).all()


@router.post("/query", response_model=DocumentQueryResponse)
def query_uploaded_documents(payload: DocumentQueryRequest):
    try:
        result = rag_retriever.answer_query(payload.query)
        return DocumentQueryResponse(
            query=payload.query,
            answer=result.get("answer", "No answer generated."),
            sources=result.get("sources", []),
        )
    except Exception as e:
        logger.error(f"RAG document query error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error querying documents: {str(e)}")