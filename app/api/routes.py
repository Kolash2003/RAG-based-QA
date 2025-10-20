from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse
from datetime import datetime
from pathlib import Path
import uuid
import shutil
from typing import Dict

from app.models.schemas import (
    UploadResponse, QueryRequest, QueryResponse, 
    HealthResponse, ErrorResponse, SourceDocument
)
from app.services.document_processor import document_processor
from app.services.vector_store import vector_store
from app.services.llm_service import llm_service
from app.config import settings
from app.utils.logger import logger

router = APIRouter()

COLLECTION_NAME = "documents"
vector_store.create_collection(COLLECTION_NAME)


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        environment=settings.app_env,
        vector_store=vector_store.get_collection_stats()
    )


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and process a document.
    
    Supported formats: PDF, TXT, DOCX, PPTX, XLSX, CSV
    """
    try:
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        
        if file_size > settings.max_upload_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum limit of {settings.max_upload_size} bytes"
            )
        
        if not document_processor.is_supported(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format. Supported: {list(document_processor.SUPPORTED_FORMATS.keys())}"
            )
        
        document_id = str(uuid.uuid4())

        upload_dir = Path("./data/uploads")
        file_path = upload_dir / f"{document_id}_{file.filename}"
        
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info("file_uploaded", filename=file.filename, document_id=document_id)
        
        text = document_processor.extract_text(str(file_path))
        
        chunks = document_processor.chunk_text(
            text,
            metadata={
                "filename": file.filename,
                "document_id": document_id,
                "uploaded_at": datetime.utcnow().isoformat()
            }
        )
        
        vector_store.add_documents(chunks, document_id)
        
        return UploadResponse(
            document_id=document_id,
            filename=file.filename,
            num_chunks=len(chunks),
            message="Document uploaded and processed successfully",
            uploaded_at=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("upload_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}"
        )


@router.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """
    Ask a question based on uploaded documents.
    """
    try:
        # Search for relevant documents
        search_results = vector_store.search(
            request.question,
            top_k=request.top_k
        )
        
        if not search_results:
            return QueryResponse(
                question=request.question,
                answer="No relevant documents found to answer this question.",
                sources=[],
                num_sources=0
            )
        
        result = llm_service.generate_answer(request.question, search_results)

        sources = [
            SourceDocument(
                text=res['text'][:500] + "..." if len(res['text']) > 500 else res['text'],
                metadata=res['metadata'],
                relevance_score=1 - res['distance']
            )
            for res in search_results
        ]
        
        return QueryResponse(
            question=request.question,
            answer=result['answer'],
            sources=sources,
            num_sources=result['num_sources']
        )
        
    except Exception as e:
        logger.error("query_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process query: {str(e)}"
        )


@router.delete("/document/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and all its chunks from the vector store."""
    try:
        vector_store.delete_document(document_id)
        
        upload_dir = Path("./data/uploads")
        for file in upload_dir.glob(f"{document_id}_*"):
            file.unlink()
        
        return {"message": f"Document {document_id} deleted successfully"}
        
    except Exception as e:
        logger.error("delete_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.get("/stats")
async def get_stats():
    """Get statistics about the vector store."""
    try:
        stats = vector_store.get_collection_stats()
        return stats
    except Exception as e:
        logger.error("stats_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )