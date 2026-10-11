from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import get_search_service
from app.api.schemas.search import (
    SearchRequest,
    SearchResponse,
    SearchResultSchema,
)
from app.retrieval.service import SearchService

router = APIRouter(prefix="/search", tags=["search"])


@router.post(
    "",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Tìm kiếm ngữ nghĩa (Semantic Search)",
)
def search_documents(
    request: SearchRequest,
    search_service: Annotated[SearchService, Depends(get_search_service)],
) -> SearchResponse:
    """Tìm kiếm ngữ nghĩa trên toàn bộ kho tài liệu hoặc theo document_id cụ thể."""
    search_results = search_service.search(
        query=request.query,
        top_k=request.top_k,
        document_id=request.document_id,
    )

    # Chuyển đổi SearchResult sang SearchResultSchema
    formatted_results = [
        SearchResultSchema(
            chunk_id=result.chunk_id,
            document_id=result.document_id,
            text=result.text,
            page_numbers=list(result.page_numbers),
            score=result.score,
        )
        for result in search_results
    ]

    return SearchResponse(
        query=request.query,
        total_results=len(formatted_results),
        results=formatted_results,
    )