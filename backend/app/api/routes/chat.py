from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from app.core.rag_pipeline import get_rag_pipeline
from app.models.schemas import ChatRequest, ChatResponse, SourceChunk
from app.utils.logger import logger

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if request.stream:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use o endpoint /chat/stream para streaming.",
        )

    try:
        pipeline = get_rag_pipeline()
        result = await pipeline.arun(
            query=request.query,
            document_id=request.document_id,
            top_k=request.top_k,
            use_reranker=request.use_reranker,
        )

        sources = [
            SourceChunk(
                content=s["content"],
                score=s["score"],
                document_id=s["document_id"],
                chunk_index=s["chunk_index"],
                rerank_score=s.get("rerank_score"),
            )
            for s in result["sources"]
        ]

        return ChatResponse(
            answer=result["answer"],
            sources=sources,
            query=result["query"],
            total_sources_found=result["total_sources_found"],
        )

    except Exception as e:
        logger.error(f"Erro no pipeline RAG: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    async def event_generator():
        try:
            pipeline = get_rag_pipeline()
            async for token in pipeline.astream(
                query=request.query,
                document_id=request.document_id,
                top_k=request.top_k,
                use_reranker=request.use_reranker,
            ):
                yield f"data: {token}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Erro no streaming: {e}")
            yield f"data: [ERROR] {str(e)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
