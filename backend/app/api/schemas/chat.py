import datetime
from typing import Any

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
    session_id: str | None = Field(
        default=None,
        description="(Tùy chọn) ID của phiên trò chuyện. Nếu không cung cấp, hệ thống sẽ tự động tạo phiên mới.",
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

    session_id: str = Field(..., description="ID định danh phiên trò chuyện")
    answer: str = Field(..., description="Câu trả lời của trợ lý kèm trích dẫn [Nguồn X]")
    sources: list[SourceSchema] = Field(
        default_factory=list, description="Danh sách các nguồn trích dẫn"
    )
    model: str = Field(..., description="Tên mô hình LLM đã thực hiện sinh câu trả lời")
    usage: TokenUsageSchema = Field(..., description="Thống kê lượng token đã sử dụng")


class ChatMessageSchema(BaseModel):
    """Schema mô tả một tin nhắn trong lịch sử chat."""

    id: str = Field(..., description="ID tin nhắn")
    role: str = Field(..., description="Vai trò: user hoặc assistant")
    content: str = Field(..., description="Nội dung tin nhắn")
    sources: list[dict[str, Any]] | None = Field(default=None, description="Trích dẫn nguồn")
    tokens_used: dict[str, int] | None = Field(default=None, description="Lượng token sử dụng")
    created_at: datetime.datetime = Field(..., description="Thời gian tạo")


class ChatSessionSchema(BaseModel):
    """Schema thông tin phiên trò chuyện."""

    id: str = Field(..., description="ID phiên trò chuyện")
    title: str = Field(..., description="Tiêu đề phiên trò chuyện")
    created_at: datetime.datetime = Field(..., description="Thời gian tạo")
    updated_at: datetime.datetime = Field(..., description="Thời gian cập nhật gần nhất")


class ChatSessionDetailSchema(ChatSessionSchema):
    """Schema chi tiết phiên trò chuyện kèm toàn bộ tin nhắn."""

    messages: list[ChatMessageSchema] = Field(default_factory=list, description="Lịch sử các tin nhắn")

