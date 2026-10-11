from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_rag_service
from app.api.schemas.chat import (
    ChatRequest,
    ChatResponse,
    SourceSchema,
    TokenUsageSchema,
)
from app.rag.service import RAGService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Hỏi đáp thông minh trên tài liệu (RAG Chat)",
)
def chat_with_documents(
    payload: ChatRequest,
    rag_service: Annotated[RAGService, Depends(get_rag_service)],
) -> ChatResponse:
    """Thực hiện hỏi đáp ngữ cảnh trên tài liệu với trích dẫn nguồn."""
    try:
        rag_answer = rag_service.answer_question(
            query=payload.query,
            document_id=payload.document_id,
            top_k=payload.top_k,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    # Format danh sách nguồn bằng chứng
    sources = [
        SourceSchema(
            source_index=src.source_index,
            chunk_id=src.chunk_id,
            document_id=src.document_id,
            page_numbers=list(src.page_numbers),
            snippet=src.snippet,
        )
        for src in rag_answer.sources
    ]

    # Format thống kê token
    usage = TokenUsageSchema(
        prompt_tokens=rag_answer.tokens_used.get("prompt_tokens", 0),
        completion_tokens=rag_answer.tokens_used.get("completion_tokens", 0),
        total_tokens=rag_answer.tokens_used.get("total_tokens", 0),
    )

    return ChatResponse(
        answer=rag_answer.answer,
        sources=sources,
        model=rag_answer.model_name,
        usage=usage,
    )
