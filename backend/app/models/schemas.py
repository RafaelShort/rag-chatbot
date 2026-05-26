from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


# Documentos
class IngestTextRequest(BaseModel):
    text: str = Field(..., min_length=10, description="Texto a ser ingerido")
    title: str = Field(default="documento", description="Titulo do documento")
    metadata: dict[str, Any] = Field(default_factory=dict)


class IngestResponse(BaseModel):
    document_id: str
    filename: str
    chunks_indexed: int
    total_chars: int
    strategy: str = ""


class DocumentInfo(BaseModel):
    document_id: str
    filename: str
    file_type: str
    chunks_count: int


class DeleteDocumentRequest(BaseModel):
    document_id: str


class CollectionInfoResponse(BaseModel):
    name: str
    vectors_count: int | None
    points_count: int | None
    status: str


# Chat / RAG
class ChatRequest(BaseModel):
    query: str = Field(..., min_length=3, description="Pergunta do usuario")
    document_id: str | None = Field(
        default=None, description="Filtrar por documento especifico"
    )
    top_k: int = Field(default=5, ge=1, le=50)
    use_reranker: bool = Field(default=True)
    stream: bool = Field(default=False)


class SourceChunk(BaseModel):
    content: str
    score: float
    document_id: str
    chunk_index: int
    rerank_score: float | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]
    query: str
    total_sources_found: int


# Health
class HealthResponse(BaseModel):
    status: str
    provider: str
    model: str
    qdrant_url: str
    collection_info: dict[str, Any] | None = None
