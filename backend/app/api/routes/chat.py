from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_chat_repo, get_rag_service
from app.api.schemas.chat import (
    ChatMessageSchema,
    ChatRequest,
    ChatResponse,
    ChatSessionDetailSchema,
    ChatSessionSchema,
    SourceSchema,
    TokenUsageSchema,
)
from app.db.repositories.chat_repo import ChatRepository
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
    chat_repo: Annotated[ChatRepository, Depends(get_chat_repo)],
) -> ChatResponse:
    """Thực hiện hỏi đáp ngữ cảnh trên tài liệu với trích dẫn nguồn và lưu lịch sử."""
    if not payload.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Câu hỏi không được để trống hoặc chỉ chứa khoảng trắng.",
        )

    # Xử lý placeholder mặc định của Swagger UI ("string" hoặc chuỗi rỗng)
    clean_session_id = payload.session_id if payload.session_id not in ("", "string") else None
    clean_document_id = payload.document_id if payload.document_id not in ("", "string") else None

    if clean_session_id:
        session = chat_repo.get_session(clean_session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy phiên trò chuyện với ID: {clean_session_id}",
            )
    else:
        title = payload.query.strip()[:60]
        session = chat_repo.create_session(title=title)

    chat_repo.add_message(
        session_id=session.id,
        role="user",
        content=payload.query,
    )

    try:
        rag_answer = rag_service.answer_question(
            query=payload.query,
            document_id=clean_document_id,
            top_k=payload.top_k,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

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

    usage = TokenUsageSchema(
        prompt_tokens=rag_answer.tokens_used.get("prompt_tokens", 0),
        completion_tokens=rag_answer.tokens_used.get("completion_tokens", 0),
        total_tokens=rag_answer.tokens_used.get("total_tokens", 0),
    )

    sources_data = [src.model_dump() for src in sources]
    usage_data = usage.model_dump()
    chat_repo.add_message(
        session_id=session.id,
        role="assistant",
        content=rag_answer.answer,
        sources=sources_data,
        tokens_used=usage_data,
    )

    return ChatResponse(
        session_id=session.id,
        answer=rag_answer.answer,
        sources=sources,
        model=rag_answer.model_name,
        usage=usage,
    )


@router.get(
    "/sessions",
    response_model=list[ChatSessionSchema],
    summary="Lấy danh sách các phiên trò chuyện",
)
def list_chat_sessions(
    chat_repo: Annotated[ChatRepository, Depends(get_chat_repo)],
) -> list[ChatSessionSchema]:
    """Lấy danh sách toàn bộ các phiên trò chuyện theo thứ tự cập nhật mới nhất."""
    sessions = chat_repo.list_sessions()
    return [
        ChatSessionSchema(
            id=s.id,
            title=s.title,
            created_at=s.created_at,
            updated_at=s.updated_at,
        )
        for s in sessions
    ]


@router.get(
    "/sessions/{session_id}",
    response_model=ChatSessionDetailSchema,
    summary="Lấy chi tiết và lịch sử tin nhắn của phiên trò chuyện",
)
def get_chat_session_detail(
    session_id: str,
    chat_repo: Annotated[ChatRepository, Depends(get_chat_repo)],
) -> ChatSessionDetailSchema:
    """Lấy chi tiết phiên trò chuyện kèm toàn bộ các tin nhắn đã trao đổi."""
    session = chat_repo.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy phiên trò chuyện với ID: {session_id}",
        )
    messages = chat_repo.get_session_history(session_id)
    return ChatSessionDetailSchema(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=[
            ChatMessageSchema(
                id=m.id,
                role=m.role,
                content=m.content,
                sources=m.sources,
                tokens_used=m.tokens_used,
                created_at=m.created_at,
            )
            for m in messages
        ],
    )


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa một phiên trò chuyện",
)
def delete_chat_session(
    session_id: str,
    chat_repo: Annotated[ChatRepository, Depends(get_chat_repo)],
) -> None:
    """Xóa phiên trò chuyện và toàn bộ lịch sử tin nhắn liên quan."""
    deleted = chat_repo.delete_session(session_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy phiên trò chuyện với ID: {session_id}",
        )

