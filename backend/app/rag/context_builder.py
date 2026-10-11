from collections.abc import Sequence
from dataclasses import dataclass

import tiktoken

from app.retrieval.models import SearchResult


@dataclass(frozen=True)
class CitationSource:
    source_index: int
    chunk_id: str
    document_id: str
    page_numbers: tuple[int, ...]
    snippet: str


@dataclass(frozen=True)
class BuiltContext:
    context_text: str
    sources: list[CitationSource]
    total_tokens: int


class ContextBuilder:
    """Xây dựng khối ngữ cảnh có kiểm soát ngân sách token từ kết quả truy hồi."""

    def __init__(self, max_context_tokens: int = 2000) -> None:
        self.max_context_tokens = max_context_tokens
        self.encoding = tiktoken.get_encoding("cl100k_base")

    def _count_tokens(self, text: str) -> int:
        return len(self.encoding.encode(text))

    def build(self, search_results: Sequence[SearchResult]) -> BuiltContext:
        """Định dạng từng chunk theo template chuẩn, kiểm tra token count không vượt quá ngân sách."""
        formatted_chunks: list[str] = []
        sources: list[CitationSource] = []
        accumulated_tokens = 0

        for idx, result in enumerate(search_results, start=1):
            text = result.text.strip()
            if not text:
                continue

            # Định dạng theo chuẩn [Nguồn X]
            chunk_block = f"[Nguồn {idx}]\n{text}"
            chunk_tokens = self._count_tokens(chunk_block)

            # Nếu thêm chunk này làm vượt quá ngân sách token tối đa thì dừng
            if accumulated_tokens + chunk_tokens > self.max_context_tokens:
                break

            accumulated_tokens += chunk_tokens
            formatted_chunks.append(chunk_block)

            # Trích đoạn ngắn snippet (tối đa 200 ký tự) cho nguồn
            snippet = text[:200] + ("..." if len(text) > 200 else "")
            sources.append(
                CitationSource(
                    source_index=idx,
                    chunk_id=result.chunk_id,
                    document_id=result.document_id,
                    page_numbers=result.page_numbers,
                    snippet=snippet,
                )
            )

        context_text = "\n\n".join(formatted_chunks)

        return BuiltContext(
            context_text=context_text,
            sources=sources,
            total_tokens=accumulated_tokens,
        )
