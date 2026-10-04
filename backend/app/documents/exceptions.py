class DocumentError(Exception):
    """Lỗi cơ sở cho toàn bộ xử lý nghiệp vụ tài liệu."""


class InvalidDocumentError(DocumentError):
    """File không tồn tại, đường dẫn sai hoặc file PDF hỏng."""


class NoExtractableTextError(DocumentError):
    """File PDF mở được nhưng không chứa chữ (thường là PDF scan dạng ảnh thuần)."""