import tiktoken

from app.documents.models import Chunk, PageText


class TokenChunker:
    def __init__(self, chunk_size_tokens: int = 512, overlap_tokens: int = 64) -> None:
        if chunk_size_tokens <= 0:
            raise ValueError("chunk_size_tokens phải lớn hơn 0")
        if overlap_tokens < 0 or overlap_tokens >= chunk_size_tokens:
            raise ValueError("overlap_tokens phải nằm trong khoảng từ 0 đến chunk_size_tokens - 1")

        self.chunk_size_tokens = chunk_size_tokens
        self.overlap_tokens = overlap_tokens
        # Tạm thời dùng cl100k_base. Sẽ cấu hình theo tokenizer của embedding model ở Phase 2.
        self.encoding = tiktoken.get_encoding("cl100k_base")

    def chunk_pages(self, document_id: str, pages: tuple[PageText, ...]) -> tuple[Chunk, ...]:
        chunks: list[Chunk] = []
        sequence = 1

        for page in pages:
            if not page.text.strip():
                continue

            token_ids = self.encoding.encode(page.text)
            start = 0
            stride = self.chunk_size_tokens - self.overlap_tokens

            while start < len(token_ids):
                end = min(start + self.chunk_size_tokens, len(token_ids))
                slice_ids = token_ids[start:end]

                # Decode an toàn, tránh lỗi vỡ byte
                chunk_text = self.encoding.decode(slice_ids, errors="replace").strip()

                if chunk_text:
                    chunks.append(
                        Chunk(
                            chunk_id=f"{document_id}_chunk_{sequence:04d}",
                            document_id=document_id,
                            text=chunk_text,
                            token_count=len(slice_ids),
                            page_numbers=(page.page_number,),
                        )
                    )
                    sequence += 1

                if end == len(token_ids):
                    break

                start += stride

        return tuple(chunks)