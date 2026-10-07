from pydantic import BaseModel, Field


class ChunkSchema(BaseModel):
    """Schema mô tả một đoạn văn bản (Chunk) trả về trong API."""

    chunk_id: str = Field(..., description="ID định danh duy nhất của chunk")
    document_id: str = Field(..., description="ID của tài liệu chứa chunk này")
    text: str = Field(..., description="Nội dung văn bản của đoạn trích")
    page_numbers: list[int] = Field(..., description="Danh sách các trang chứa đoạn văn")
    token_count: int = Field(..., description="Số lượng tokens của chunk")


class DocumentUploadResponse(BaseModel):
    """Schema kết quả sau khi upload và xử lý tài liệu PDF thành công."""

    document_id: str = Field(..., description="ID định danh của tài liệu")
    filename: str = Field(..., description="Tên tệp gốc tải lên")
    page_count: int = Field(..., description="Tổng số trang của tài liệu")
    chunk_count: int = Field(..., description="Tổng số chunks đã được cắt và vector hóa")
    message: str = Field(default="Tài liệu đã được tải lên và lập chỉ mục thành công.")


class DocumentDetailResponse(BaseModel):
    """Schema chi tiết tài liệu."""

    document_id: str
    filename: str
    page_count: int
    chunks: list[ChunkSchema]
