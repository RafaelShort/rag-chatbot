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
