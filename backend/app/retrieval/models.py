from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class VectorRecord:
    """Bản ghi vector lưu trữ trong Vector Database kèm dữ liệu bổ trợ (Payload)."""

    id: str
    vector: list[float]
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SearchResult:
    """Kết quả tìm kiếm ngữ nghĩa trả về cho người dùng kèm nguồn gốc đoạn văn."""

    chunk_id: str
    document_id: str
    text: str
    page_numbers: tuple[int, ...]
    score: float
