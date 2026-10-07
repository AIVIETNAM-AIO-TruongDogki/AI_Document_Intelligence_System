from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import get_search_service
from app.api.schemas.search import (
    SearchRequest,
    SearchResponse,
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
    """API tìm kiếm ngữ nghĩa:
    
    Yêu cầu:
    1. Gọi search_service.search(query=request.query, top_k=request.top_k, document_id=request.document_id)
    2. Format danh sách SearchResult sang danh sách SearchResultSchema
    3. Trả về SearchResponse(query=request.query, total_results=len(formatted_results), results=formatted_results)
    """
    # TODO: Bạn hãy tự code ở đây theo các bước hướng dẫn trên:
    raise NotImplementedError("Hãy tự code endpoint search_documents")
