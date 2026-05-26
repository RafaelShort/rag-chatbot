from __future__ import annotations

from typing import Any, AsyncIterator
from functools import lru_cache

from app.config import get_settings
from app.utils.logger import logger
from app.core.embeddings import get_embedding_manager
from app.core.retriever import get_retriever
from app.core.reranker import get_reranker
from app.core.llm import get_llm_manager

settings = get_settings()


class RAGPipeline:
    def __init__(self) -> None:
        self.embedding_manager = get_embedding_manager()
        self.retriever = get_retriever()
        self.reranker = get_reranker()
        self.llm_manager = get_llm_manager()
        logger.info("RAGPipeline iniciado")

    # Pipeline principal
    def run(
        self,
        query: str,
        document_id: str | None = None,
        top_k: int | None = None,
        use_reranker: bool = True,
    ) -> dict[str, Any]:
        logger.info(f"RAG run query_chars={len(query)} doc={document_id}")

        # 1. Embed query
        query_embedding = self.embedding_manager.embed_query(query)

        # 2. Retrieve
        k = top_k or settings.retrieval_top_k
        results = self.retriever.search(
            query_embedding=query_embedding,
            top_k=k,
            document_id=document_id,
        )

        if not results:
            logger.warning("Nenhum resultado encontrado no vector store")
            return {
                "answer": "Nao encontrei informacoes relevantes nos documentos.",
                "sources": [],
                "query": query,
                "total_sources_found": 0,
            }

        # 3. Rerank
        if use_reranker and settings.use_reranker:
            results = self.reranker.rerank(
                query=query,
                results=results,
                top_k=settings.reranker_top_k,
            )
        else:
            results = results[: settings.reranker_top_k]

        # 4. Montar contexto
        context = self._build_context(results)

        # 5. Gerar resposta
        answer = self.llm_manager.generate(query=query, context=context)

        return {
            "answer": answer,
            "sources": results,
            "query": query,
            "total_sources_found": len(results),
        }

    async def arun(
        self,
        query: str,
        document_id: str | None = None,
        top_k: int | None = None,
        use_reranker: bool = True,
    ) -> dict[str, Any]:
        logger.info(f"RAG arun query_chars={len(query)} doc={document_id}")

        query_embedding = self.embedding_manager.embed_query(query)

        k = top_k or settings.retrieval_top_k
        results = self.retriever.search(
            query_embedding=query_embedding,
            top_k=k,
            document_id=document_id,
        )

        if not results:
            return {
                "answer": "Nao encontrei informacoes relevantes nos documentos.",
                "sources": [],
                "query": query,
                "total_sources_found": 0,
            }

        if use_reranker and settings.use_reranker:
            results = self.reranker.rerank(
                query=query,
                results=results,
                top_k=settings.reranker_top_k,
            )
        else:
            results = results[: settings.reranker_top_k]

        context = self._build_context(results)
        answer = await self.llm_manager.agenerate(query=query, context=context)

        return {
            "answer": answer,
            "sources": results,
            "query": query,
            "total_sources_found": len(results),
        }

    async def astream(
        self,
        query: str,
        document_id: str | None = None,
        top_k: int | None = None,
        use_reranker: bool = True,
    ) -> AsyncIterator[str]:
        query_embedding = self.embedding_manager.embed_query(query)

        k = top_k or settings.retrieval_top_k
        results = self.retriever.search(
            query_embedding=query_embedding,
            top_k=k,
            document_id=document_id,
        )

        if not results:
            yield "Nao encontrei informacoes relevantes nos documentos."
            return

        if use_reranker and settings.use_reranker:
            results = self.reranker.rerank(
                query=query,
                results=results,
                top_k=settings.reranker_top_k,
            )
        else:
            results = results[: settings.reranker_top_k]

        context = self._build_context(results)

        async for token in self.llm_manager.astream(query=query, context=context):
            yield token

    # Helpers
    @staticmethod
    def _build_context(results: list[dict[str, Any]]) -> str:
        parts = []
        for i, r in enumerate(results, 1):
            doc_id = r.get("document_id", "desconhecido")
            score = r.get("rerank_score") or r.get("score", 0)
            parts.append(
                f"[Fonte {i} | doc={doc_id} | score={score:.4f}]\n{r['content']}"
            )
        return "\n\n---\n\n".join(parts)


@lru_cache
def get_rag_pipeline() -> RAGPipeline:
    return RAGPipeline()
