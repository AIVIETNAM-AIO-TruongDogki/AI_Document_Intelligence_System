from dataclasses import dataclass


@dataclass(frozen=True)
class PageText:
    """Nội dung văn bản thô trích xuất từ 1 trang PDF."""
    page_number: int  # Bắt đầu từ 1 (chuẩn theo số trang người dùng đọc)
    text: str


@dataclass(frozen=True)
class DocumentMetadata:
    """Thông tin tổng quát của tài liệu."""
    document_id: str
    filename: str
    page_count: int


@dataclass(frozen=True)
class Chunk:
    """Một đoạn văn bản đã được cắt nhỏ để chuẩn bị nhúng vector."""
    chunk_id: str                  # Định danh có thể tái lập: {document_id}_chunk_0001
    document_id: str
    text: str
    token_count: int
    page_numbers: tuple[int, ...]  # Danh sách trang nguồn (hỗ trợ đoạn vắt ngang nhiều trang)


@dataclass(frozen=True)
class ParsedDocument:
    """Kết quả hoàn chỉnh của toàn bộ pipeline xử lý tài liệu."""
    metadata: DocumentMetadata
    pages: tuple[PageText, ...]
    chunks: tuple[Chunk, ...]