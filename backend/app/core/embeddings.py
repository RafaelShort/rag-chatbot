from __future__ import annotations

from functools import lru_cache
from typing import Any

from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings

from app.config import get_settings
from app.utils.logger import logger

settings = get_settings()


class EmbeddingManager:
    def __init__(self) -> None:
        self._model: Any = None
        self._provider = settings.llm_provider
        logger.info(f"EmbeddingManager iniciado provider={self._provider}")

    @property
    def model(self) -> Any:
        if self._model is None:
            self._model = self._load_model()
        return self._model

    def _load_model(self) -> Any:
        if self._provider == "openai":
            logger.info(f"Carregando embeddings OpenAI: {settings.embedding_model}")
            return OpenAIEmbeddings(
                model=settings.embedding_model,
                openai_api_key=settings.openai_api_key,
            )
        logger.info("Carregando embeddings HuggingFace (local)")
        return HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

    def embed_query(self, text: str) -> list[float]:
        logger.debug(f"Embed query chars={len(text)}")
        return self.model.embed_query(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        logger.info(f"Embed documents total={len(texts)}")
        return self.model.embed_documents(texts)

    def get_langchain_embeddings(self) -> Any:
        return self.model


@lru_cache
def get_embedding_manager() -> EmbeddingManager:
    return EmbeddingManager()

