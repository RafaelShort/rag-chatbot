from __future__ import annotations

from typing import Any
from functools import lru_cache

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)

from app.config import get_settings
from app.utils.logger import logger
from app.core.chunker import Chunk

settings = get_settings()


class VectorRetriever:
    def __init__(self) -> None:
        self._client: QdrantClient | None = None
        logger.info(f"VectorRetriever iniciado url={settings.qdrant_url}")

    @property
    def client(self) -> QdrantClient:
        if self._client is None:
            self._client = QdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port,
            )
            logger.info("Conexao com Qdrant estabelecida")
        return self._client

    # Gerenciamento da collection
    def ensure_collection(self, dimension: int | None = None) -> None:
        dim = dimension or settings.embedding_dimension
        collections = [c.name for c in self.client.get_collections().collections]

        if settings.qdrant_collection not in collections:
            self.client.create_collection(
                collection_name=settings.qdrant_collection,
                vectors_config=VectorParams(
                    size=dim,
                    distance=Distance.COSINE,
                ),
            )
            logger.info(f"Collection criada: {settings.qdrant_collection} dim={dim}")
        else:
            logger.info(f"Collection ja existe: {settings.qdrant_collection}")

    def delete_collection(self) -> None:
        self.client.delete_collection(settings.qdrant_collection)
        logger.warning(f"Collection deletada: {settings.qdrant_collection}")

    def get_collection_info(self) -> dict[str, Any]:
        info = self.client.get_collection(settings.qdrant_collection)
        return {
            "name": settings.qdrant_collection,
            "vectors_count": info.vectors_count,
            "points_count": info.points_count,
            "status": str(info.status),
        }

    # Indexacao
    def index_chunks(
        self,
        chunks: list[Chunk],
        embeddings: list[list[float]],
        document_id: str,
    ) -> int:
        if len(chunks) != len(embeddings):
            raise ValueError(
                f"Chunks ({len(chunks)}) e embeddings ({len(embeddings)}) "
                "devem ter o mesmo tamanho."
            )

        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            point_id = abs(hash(f"{document_id}_{i}")) % (2**63)
            payload = {
                "content": chunk.content,
                "document_id": document_id,
                "chunk_index": chunk.chunk_index,
                "total_chunks": chunk.total_chunks,
                "start_char": chunk.start_char,
                "end_char": chunk.end_char,
                "word_count": chunk.word_count,
                **chunk.metadata,
            }
            points.append(
                PointStruct(id=point_id, vector=embedding, payload=payload)
            )

        self.client.upsert(
            collection_name=settings.qdrant_collection,
            points=points,
        )

        logger.info(f"Indexados {len(points)} chunks do documento {document_id}")
        return len(points)

    def delete_document(self, document_id: str) -> None:
        self.client.delete(
            collection_name=settings.qdrant_collection,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id),
                    )
                ]
            ),
        )
        logger.info(f"Documento removido do vector store: {document_id}")

    def list_documents(self) -> list[dict[str, Any]]:
        """Lista todos os documentos unicos na collection."""
        documents: dict[str, dict] = {}
        offset = None

        while True:
            results, next_offset = self.client.scroll(
                collection_name=settings.qdrant_collection,
                limit=100,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )

            for point in results:
                payload = point.payload or {}
                doc_id = payload.get("document_id")
                if not doc_id:
                    continue
                if doc_id not in documents:
                    documents[doc_id] = {
                        "document_id": doc_id,
                        "filename": payload.get("filename", "desconhecido"),
                        "file_type": payload.get("file_type", "text"),
                        "chunks_count": 0,
                    }
                documents[doc_id]["chunks_count"] += 1

            if next_offset is None:
                break
            offset = next_offset

        logger.info(f"Listados {len(documents)} documentos unicos")
        return list(documents.values())

    # Busca
    def search(
        self,
        query_embedding: list[float],
        top_k: int | None = None,
        document_id: str | None = None,
    ) -> list[dict[str, Any]]:
        k = top_k or settings.retrieval_top_k

        search_filter = None
        if document_id:
            search_filter = Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id),
                    )
                ]
            )

        results = self.client.search(
            collection_name=settings.qdrant_collection,
            query_vector=query_embedding,
            limit=k,
            query_filter=search_filter,
            with_payload=True,
        )

        hits = []
        for r in results:
            hits.append(
                {
                    "content": r.payload.get("content", ""),
                    "score": r.score,
                    "document_id": r.payload.get("document_id", ""),
                    "chunk_index": r.payload.get("chunk_index", 0),
                    "metadata": {
                        k: v
                        for k, v in r.payload.items()
                        if k not in ("content", "document_id")
                    },
                }
            )

        logger.info(f"Busca retornou {len(hits)} resultados top_k={k}")
        return hits


@lru_cache
def get_retriever() -> VectorRetriever:
    return VectorRetriever()
