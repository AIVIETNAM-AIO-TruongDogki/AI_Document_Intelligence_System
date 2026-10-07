from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Schema request tìm kiếm ngữ nghĩa."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Nội dung câu hỏi hoặc từ khóa tìm kiếm",
        examples=["Các điều khoản bồi thường hợp đồng là gì?"],
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Số lượng đoạn trích liên quan nhất cần trả về",
    )
    document_id: str | None = Field(
        default=None,
        description="(Tùy chọn) Chỉ tìm kiếm trong một tài liệu cụ thể",
    )


class SearchResultSchema(BaseModel):
    """Schema chi tiết của 1 kết quả tìm kiếm ngữ nghĩa."""

    chunk_id: str
    document_id: str
    text: str
    page_numbers: list[int]
    score: float = Field(..., description="Điểm tương đồng Cosine Similarity (0.0 đến 1.0)")


class SearchResponse(BaseModel):
    """Schema danh sách kết quả tìm kiếm trả về."""

    query: str
    total_results: int
    results: list[SearchResultSchema]
