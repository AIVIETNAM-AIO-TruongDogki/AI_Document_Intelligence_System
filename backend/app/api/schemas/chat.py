from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Schema dữ liệu gửi lên khi người dùng đặt câu hỏi."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Nội dung câu hỏi của người dùng",
        examples=["Chính sách nghỉ phép quy định bao nhiêu ngày?"],
    )
    document_id: str | None = Field(
        default=None,
        description="(Tùy chọn) Chỉ hỏi đáp trong phạm vi tài liệu có ID này",
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Số lượng đoạn văn bản liên quan nhất được dùng làm ngữ cảnh",
    )


class SourceSchema(BaseModel):
    """Schema thông tin trích dẫn nguồn bằng chứng."""

    source_index: int = Field(..., description="Chỉ số thứ tự của nguồn trong ngữ cảnh [Nguồn X]")
    chunk_id: str = Field(..., description="ID của đoạn trích")
    document_id: str = Field(..., description="ID của tài liệu gốc")
    page_numbers: list[int] = Field(
        default_factory=list, description="Danh sách các trang chứa đoạn trích"
    )
    snippet: str = Field(..., description="Trích đoạn ngắn nội dung làm bằng chứng")


class TokenUsageSchema(BaseModel):
    """Schema thống kê token tiêu thụ."""

    prompt_tokens: int = Field(default=0, description="Số token trong prompt")
    completion_tokens: int = Field(default=0, description="Số token trong câu trả lời")
    total_tokens: int = Field(default=0, description="Tổng số token đã sử dụng")


class ChatResponse(BaseModel):
    """Schema kết quả phản hồi từ hệ thống RAG."""

    answer: str = Field(..., description="Câu trả lời của trợ lý kèm trích dẫn [Nguồn X]")
    sources: list[SourceSchema] = Field(
        default_factory=list, description="Danh sách các nguồn trích dẫn"
    )
    model: str = Field(..., description="Tên mô hình LLM đã thực hiện sinh câu trả lời")
    usage: TokenUsageSchema = Field(..., description="Thống kê lượng token đã sử dụng")
