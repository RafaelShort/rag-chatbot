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
        paragraphs = re.split(r"\n{2,}", text)
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
                buffer = overlap_text + "\n\n" + para
                buffer_start = char_cursor
            else:
                buffer = (buffer + "\n\n" + para).strip() if buffer else para
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
        sentences = re.split(r"(?<=[.!?])\s+", text)
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
        text = re.sub(r"\r\n", "\n", text)
        text = re.sub(r"\t", " ", text)
        text = re.sub(r" {2,}", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    @staticmethod
    def _last_sentences(text: str, max_chars: int) -> str:
        sentences = re.split(r"(?<=[.!?])\s+", text)
        overlap = ""
        for sentence in reversed(sentences):
            if len(overlap) + len(sentence) <= max_chars:
                overlap = sentence + " " + overlap
            else:
                break
        return overlap.strip()
