from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.config import get_settings
from app.models.schemas import DeleteDocumentRequest, DocumentInfo, IngestResponse, IngestTextRequest
from app.services.document_service import DocumentService
from app.utils.logger import logger

router = APIRouter(prefix="/documents", tags=["Documents"])
settings = get_settings()

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".md"}


def get_document_service() -> DocumentService:
    return DocumentService()


@router.get("", response_model=list[DocumentInfo])
async def list_documents():
    try:
        service = get_document_service()
        return service.list_documents()
    except Exception as e:
        logger.error(f"Erro ao listar documentos: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/upload", response_model=IngestResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    metadata: str = Form(default="{}"),
):
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Tipo nao suportado: {suffix}. Use: {ALLOWED_EXTENSIONS}",
        )

    upload_path = settings.uploads_dir / file.filename
    try:
        with upload_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"Arquivo salvo: {upload_path}")

        import json
        extra_metadata = json.loads(metadata)

        service = get_document_service()
        result = service.ingest_file(upload_path, metadata=extra_metadata)

        return IngestResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        logger.error(f"Erro ao processar arquivo: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    finally:
        if upload_path.exists():
            upload_path.unlink()


@router.post("/ingest-text", response_model=IngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest_text(request: IngestTextRequest):
    try:
        service = get_document_service()
        result = service.ingest_text(
            text=request.text,
            title=request.title,
            metadata=request.metadata,
        )
        return IngestResponse(**result)
    except Exception as e:
        logger.error(f"Erro ao ingerir texto: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: str):
    try:
        service = get_document_service()
        service.delete_document(document_id)
    except Exception as e:
        logger.error(f"Erro ao deletar documento: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/collection/info")
async def collection_info():
    try:
        service = get_document_service()
        return service.get_collection_info()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
