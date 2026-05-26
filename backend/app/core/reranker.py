from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.config import get_settings
from app.utils.logger import logger

settings = get_settings()


class Reranker:
    """
    Re-ranking de resultados usando cross-encoder (FlagEmbedding).
    Recebe os top-K da busca vetorial e reordena por relevancia real.
    """

    def __init__(self) -> None:
        self._model: Any = None
        logger.info("Reranker iniciado")

    @property
    def model(self) -> Any:
        if self._model is None:
            self._model = self._load_model()
        return self._model

    def _load_model(self) -> Any:
        try:
            from FlagEmbedding import FlagReranker
            logger.info("Carregando FlagReranker BAAI/bge-reranker-base")
            return FlagReranker("BAAI/bge-reranker-base", use_fp16=True)
        except Exception as e:
            logger.warning(f"FlagReranker nao disponivel: {e}. Usando score original.")
            return None

    def rerank(
        self,
        query: str,
        results: list[dict[str, Any]],
        top_k: int | None = None,
    ) -> list[dict[str, Any]]:
        k = top_k or settings.reranker_top_k

        if not results:
            return []

        if self.model is None:
            logger.warning("Reranker indisponivel, retornando top_k pelo score original.")
            return sorted(results, key=lambda x: x["score"], reverse=True)[:k]

        pairs = [[query, r["content"]] for r in results]

        logger.info(f"Reranking {len(pairs)} resultados -> top {k}")

        scores = self.model.compute_score(pairs)

        if isinstance(scores, float):
            scores = [scores]

        for result, score in zip(results, scores):
            result["rerank_score"] = float(score)

        reranked = sorted(results, key=lambda x: x["rerank_score"], reverse=True)

        logger.info(
            f"Rerank concluido top score={reranked[0]['rerank_score']:.4f}"
        )
        return reranked[:k]


@lru_cache
def get_reranker() -> Reranker:
    return Reranker()
