from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.utils.logger import logger
from app.api.routes import documents, chat, health

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("RAG System iniciando...")
    logger.info(f"Provider: {settings.llm_provider} | Model: {settings.llm_model}")
    logger.info(f"Qdrant: {settings.qdrant_url}")

    try:
        from app.core.retriever import get_retriever
        get_retriever().ensure_collection()
        logger.info("Qdrant collection verificada com sucesso")
    except Exception as e:
        logger.warning(f"Qdrant indisponivel na inicializacao: {e}")

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

app.include_router(health.router)
app.include_router(documents.router)
app.include_router(chat.router)


@app.get("/", tags=["Root"])
async def root():
    return {
        "name": "RAG System API",
        "version": "1.0.0",
        "docs": "/docs",
    }
