from __future__ import annotations

import hashlib
import uuid
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.utils.logger import logger
from app.core.chunker import DocumentChunker, ChunkingStrategy, Chunk
from app.core.embeddings import get_embedding_manager
from app.core.retriever import get_retriever

settings = get_settings()


class DocumentService:
    def __init__(self) -> None:
        self.chunker = DocumentChunker(
            strategy=ChunkingStrategy(settings.chunking_strategy),
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        self.embedding_manager = get_embedding_manager()
        self.retriever = get_retriever()
        logger.info("DocumentService iniciado")


    # Ingestao principal
    def ingest_file(self, file_path: Path, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        logger.info(f"Ingerindo arquivo: {file_path.name}")

        text = self._parse_file(file_path)
        if not text:
            raise ValueError(f"Nao foi possivel extrair texto de: {file_path.name}")

        document_id = self._generate_document_id(file_path, text)

        doc_metadata = {
            "filename": file_path.name,
            "file_type": file_path.suffix.lower(),
            "document_id": document_id,
            **(metadata or {}),
        }

        chunks = self.chunker.chunk(text, metadata=doc_metadata)
        logger.info(f"Gerados {len(chunks)} chunks para {file_path.name}")

        self.retriever.ensure_collection()

        texts = [c.content for c in chunks]
        embeddings = self.embedding_manager.embed_documents(texts)

        indexed = self.retriever.index_chunks(chunks, embeddings, document_id)

        return {
            "document_id": document_id,
            "filename": file_path.name,
            "chunks_indexed": indexed,
            "total_chars": len(text),
            "strategy": settings.chunking_strategy,
        }

    def ingest_text(
        self,
        text: str,
        title: str = "documento",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        document_id = str(uuid.uuid4())

        doc_metadata = {
            "filename": title,
            "file_type": "text",
            "document_id": document_id,
            **(metadata or {}),
        }

        chunks = self.chunker.chunk(text, metadata=doc_metadata)

        self.retriever.ensure_collection()

        texts = [c.content for c in chunks]
        embeddings = self.embedding_manager.embed_documents(texts)

        indexed = self.retriever.index_chunks(chunks, embeddings, document_id)

        return {
            "document_id": document_id,
            "filename": title,
            "chunks_indexed": indexed,
            "total_chars": len(text),
        }

    def delete_document(self, document_id: str) -> None:
        self.retriever.delete_document(document_id)
        logger.info(f"Documento deletado: {document_id}")

    def list_documents(self) -> list[dict[str, Any]]:
        return self.retriever.list_documents()

    def get_collection_info(self) -> dict[str, Any]:
        return self.retriever.get_collection_info()

    # Parsers por tipo de arquivo
    def _parse_file(self, file_path: Path) -> str:
        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            return self._parse_pdf(file_path)
        elif suffix in (".docx", ".doc"):
            return self._parse_docx(file_path)
        elif suffix in (".txt", ".md", ".rst"):
            return self._parse_text(file_path)
        else:
            raise ValueError(f"Tipo de arquivo nao suportado: {suffix}")

    def _parse_pdf(self, file_path: Path) -> str:
        from pypdf import PdfReader

        reader = PdfReader(str(file_path))
        pages = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                pages.append(f"[Pagina {i + 1}]\n{text}")

        full_text = "\n\n".join(pages)
        logger.info(f"PDF parseado: {len(reader.pages)} paginas, {len(full_text)} chars")
        return full_text

    def _parse_docx(self, file_path: Path) -> str:
        from docx import Document

        doc = Document(str(file_path))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        full_text = "\n\n".join(paragraphs)
        logger.info(f"DOCX parseado: {len(paragraphs)} paragrafos, {len(full_text)} chars")
        return full_text

    def _parse_text(self, file_path: Path) -> str:
        text = file_path.read_text(encoding="utf-8")
        logger.info(f"TXT parseado: {len(text)} chars")
        return text

    # Helpers
    @staticmethod
    def _generate_document_id(file_path: Path, text: str) -> str:
        content = f"{file_path.name}_{len(text)}"
        return hashlib.md5(content.encode()).hexdigest()
