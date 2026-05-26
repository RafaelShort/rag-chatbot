Set-Content -Encoding UTF8 setup_files.py @'
import pathlib

files = {}

# ── chunker.py ──────────────────────────────────────────────────
files["backend/app/core/chunker.py"] = '''
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.config import get_settings
from app.utils.logger import logger

settings = get_settings()


class ChunkingStrategy(str, Enum):
    SLIDING_WINDOW = "sliding_window"
    SEMANTIC = "semantic"
    SENTENCE = "sentence"


@dataclass
class Chunk:
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    chunk_index: int = 0
    total_chunks: int = 0
    start_char: int = 0
    end_char: int = 0

    @property
    def char_count(self) -> int:
        return len(self.content)

    @property
    def word_count(self) -> int:
        return len(self.content.split())


class DocumentChunker:
    def __init__(
        self,
        strategy: ChunkingStrategy = ChunkingStrategy.SLIDING_WINDOW,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> None:
        self.strategy = strategy
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap

    def chunk(self, text: str, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        if not text or not text.strip():
            logger.warning("Texto vazio recebido pelo chunker.")
            return []

        metadata = metadata or {}
        text = self._clean_text(text)

        logger.info(
            f"Chunking strategy={self.strategy.value} "
            f"size={self.chunk_size} overlap={self.chunk_overlap} "
            f"chars={len(text)}"
        )

        if self.strategy == ChunkingStrategy.SLIDING_WINDOW:
            chunks = self._sliding_window(text, metadata)
        elif self.strategy == ChunkingStrategy.SEMANTIC:
            chunks = self._semantic_chunking(text, metadata)
        else:
            chunks = self._sentence_chunking(text, metadata)

        total = len(chunks)
        for i, c in enumerate(chunks):
            c.chunk_index = i
            c.total_chunks = total

        logger.info(f"Total de chunks gerados: {total}")
        return chunks

    def _sliding_window(self, text: str, metadata: dict[str, Any]) -> list[Chunk]:
        chunks: list[Chunk] = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size
            if end < len(text):
                boundary = text.rfind(" ", start, end)
                if boundary > start:
                    end = boundary

            content = text[start:end].strip()
            if content:
                chunks.append(
                    Chunk(
                        content=content,
                        metadata={**metadata, "strategy": "sliding_window"},
                        start_char=start,
                        end_char=end,
                    )
                )

            start = end - self.chunk_overlap
            if start >= len(text):
                break

        return chunks

    def _semantic_chunking(self, text: str, metadata: dict[str, Any]) -> list[Chunk]:
        paragraphs = re.split(r"\\n{2,}", text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        chunks: list[Chunk] = []
        buffer = ""
        buffer_start = 0
        char_cursor = 0

        for para in paragraphs:
            if buffer and len(buffer) + len(para) + 1 > self.chunk_size:
                chunks.append(
                    Chunk(
                        content=buffer.strip(),
                        metadata={**metadata, "strategy": "semantic"},
                        start_char=buffer_start,
                        end_char=char_cursor,
                    )
                )
                overlap_text = self._last_sentences(buffer, self.chunk_overlap)
                buffer = overlap_text + "\\n\\n" + para
                buffer_start = char_cursor
            else:
                buffer = (buffer + "\\n\\n" + para).strip() if buffer else para
                if not buffer_start:
                    buffer_start = char_cursor

            char_cursor += len(para) + 2

        if buffer.strip():
            chunks.append(
                Chunk(
                    content=buffer.strip(),
                    metadata={**metadata, "strategy": "semantic"},
                    start_char=buffer_start,
                    end_char=char_cursor,
                )
            )

        return chunks

    def _sentence_chunking(self, text: str, metadata: dict[str, Any]) -> list[Chunk]:
        sentences = re.split(r"(?<=[.!?])\\s+", text)
        sentences = [s.strip() for s in sentences if s.strip()]

        chunks: list[Chunk] = []
        buffer = ""
        start_char = 0
        char_cursor = 0

        for sentence in sentences:
            if buffer and len(buffer) + len(sentence) + 1 > self.chunk_size:
                chunks.append(
                    Chunk(
                        content=buffer.strip(),
                        metadata={**metadata, "strategy": "sentence"},
                        start_char=start_char,
                        end_char=char_cursor,
                    )
                )
                buffer = sentence
                start_char = char_cursor
            else:
                buffer = (buffer + " " + sentence).strip()

            char_cursor += len(sentence) + 1

        if buffer.strip():
            chunks.append(
                Chunk(
                    content=buffer.strip(),
                    metadata={**metadata, "strategy": "sentence"},
                    start_char=start_char,
                    end_char=char_cursor,
                )
            )

        return chunks

    @staticmethod
    def _clean_text(text: str) -> str:
        text = re.sub(r"\\r\\n", "\\n", text)
        text = re.sub(r"\\t", " ", text)
        text = re.sub(r" {2,}", " ", text)
        text = re.sub(r"\\n{3,}", "\\n\\n", text)
        return text.strip()

    @staticmethod
    def _last_sentences(text: str, max_chars: int) -> str:
        sentences = re.split(r"(?<=[.!?])\\s+", text)
        overlap = ""
        for sentence in reversed(sentences):
            if len(overlap) + len(sentence) <= max_chars:
                overlap = sentence + " " + overlap
            else:
                break
        return overlap.strip()
'''.lstrip()

# ── embeddings.py ────────────────────────────────────────────────
files["backend/app/core/embeddings.py"] = '''
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
'''.lstrip()

# ── llm.py ──────────────────────────────────────────────────────
files["backend/app/core/llm.py"] = '''
from __future__ import annotations

from functools import lru_cache
from typing import Any, AsyncIterator

from langchain_openai import ChatOpenAI
from langchain_community.llms import Ollama
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser

from app.config import get_settings
from app.utils.logger import logger

settings = get_settings()

RAG_SYSTEM_PROMPT = """Voce e um assistente especializado em responder perguntas
com base em documentos fornecidos como contexto.

Regras:
- Responda APENAS com base no contexto fornecido.
- Se a resposta nao estiver no contexto, diga: Nao encontrei essa informacao nos documentos.
- Seja objetivo e cite trechos relevantes quando possivel.
- Responda no mesmo idioma da pergunta.

Contexto:
{context}
"""


class LLMManager:
    def __init__(self) -> None:
        self._llm: Any = None
        self._provider = settings.llm_provider
        logger.info(
            f"LLMManager iniciado provider={self._provider} "
            f"model={settings.llm_model}"
        )

    @property
    def llm(self) -> Any:
        if self._llm is None:
            self._llm = self._load_llm()
        return self._llm

    def _load_llm(self) -> Any:
        if self._provider == "openai":
            logger.info(f"Carregando ChatOpenAI: {settings.llm_model}")
            return ChatOpenAI(
                model=settings.llm_model,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
                openai_api_key=settings.openai_api_key,
                streaming=True,
            )
        logger.info(f"Carregando Ollama: {settings.llm_model}")
        return Ollama(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
        )

    def generate(self, query: str, context: str) -> str:
        logger.info(f"Gerando resposta query_chars={len(query)}")
        system_content = RAG_SYSTEM_PROMPT.format(context=context)
        messages = [
            SystemMessage(content=system_content),
            HumanMessage(content=query),
        ]
        chain = self.llm | StrOutputParser()
        response = chain.invoke(messages)
        logger.info(f"Resposta gerada chars={len(response)}")
        return response

    async def agenerate(self, query: str, context: str) -> str:
        system_content = RAG_SYSTEM_PROMPT.format(context=context)
        messages = [
            SystemMessage(content=system_content),
            HumanMessage(content=query),
        ]
        chain = self.llm | StrOutputParser()
        return await chain.ainvoke(messages)

    async def astream(self, query: str, context: str) -> AsyncIterator[str]:
        system_content = RAG_SYSTEM_PROMPT.format(context=context)
        messages = [
            SystemMessage(content=system_content),
            HumanMessage(content=query),
        ]
        chain = self.llm | StrOutputParser()
        async for token in chain.astream(messages):
            yield token

    def get_langchain_llm(self) -> Any:
        return self.llm


@lru_cache
def get_llm_manager() -> LLMManager:
    return LLMManager()
'''.lstrip()

# ── logger.py ───────────────────────────────────────────────────
files["backend/app/utils/logger.py"] = '''
import sys
from loguru import logger
from app.config import get_settings

settings = get_settings()


def setup_logger() -> None:
    logger.remove()

    log_format = (
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{name}:{function}:{line} | "
        "{message}"
    )

    logger.add(
        sys.stdout,
        format=log_format,
        level="DEBUG" if settings.debug else "INFO",
        colorize=True,
    )

    logger.add(
        "logs/app_{time:YYYY-MM-DD}.log",
        format=log_format,
        level="INFO",
        rotation="00:00",
        retention="7 days",
        compression="zip",
        encoding="utf-8",
    )


setup_logger()

__all__ = ["logger"]
'''.lstrip()

# ── main.py ─────────────────────────────────────────────────────
files["backend/app/main.py"] = '''
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.utils.logger import logger

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("RAG System iniciando...")
    logger.info(f"Provider: {settings.llm_provider} | Model: {settings.llm_model}")
    logger.info(f"Qdrant: {settings.qdrant_url}")
    yield
    logger.info("RAG System encerrando...")


app = FastAPI(
    title="RAG System API",
    description="Retrieval-Augmented Generation com LangChain + Qdrant",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "provider": settings.llm_provider,
        "model": settings.llm_model,
        "qdrant_url": settings.qdrant_url,
    }
'''.lstrip()

# ── Escrever todos os arquivos ───────────────────────────────────
for path, content in files.items():
    file_path = pathlib.Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
    print(f"OK: {path}")

print("\nTodos os arquivos foram escritos com UTF-8!")
'@
