from fastapi import APIRouter
from app.config import get_settings
from app.utils.logger import logger

router = APIRouter(prefix="/health", tags=["Health"])
settings = get_settings()


@router.get("")
async def health_check():
    try:
        from app.core.retriever import get_retriever
        retriever = get_retriever()
        retriever.ensure_collection()
        collection_info = retriever.get_collection_info()
        qdrant_status = "ok"
    except Exception as e:
        logger.warning(f"Qdrant indisponivel: {e}")
        collection_info = None
        qdrant_status = "unavailable"

    return {
        "status": "ok",
        "provider": settings.llm_provider,
        "model": settings.llm_model,
        "qdrant_url": settings.qdrant_url,
        "qdrant_status": qdrant_status,
        "collection_info": collection_info,
    }
