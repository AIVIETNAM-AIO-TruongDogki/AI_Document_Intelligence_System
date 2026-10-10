import math
import re
from collections import Counter
from collections.abc import Sequence

from app.documents.models import Chunk
from app.retrieval.models import SearchResult


class BM25Retriever:
    """In-memory BM25 Okapi retriever cho Sparse Lexical Search."""

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        """Khởi tạo siêu tham số BM25.

        Args:
            k1: Điều khiển mức độ bão hòa của tần suất xuất hiện từ (TF saturation).
            b: Điều khiển mức độ phạt độ dài văn bản so với độ dài trung bình (Length normalization).
        """
        self.k1 = k1
        self.b = b
        self._corpus: dict[str, Chunk] = {}
        self._tokenized_corpus: dict[str, list[str]] = {}
        self._doc_lengths: dict[str, int] = {}
        self._avgdl: float = 0.0
        self._doc_frequencies: Counter[str] = Counter()
        self._idf: dict[str, float] = {}

    def tokenize(self, text: str) -> list[str]:
        """Tách từ đơn giản (hỗ trợ cả tiếng Anh lẫn tiếng Việt không dấu / có dấu).

        Chuyển về chữ thường, thay thế ký tự đặc biệt bằng khoảng trắng và lọc token hợp lệ.
        """
        text = text.lower()
        clean_text = re.sub(r'[^\w\s]|_', ' ', text)
        tokens = clean_text.strip().split()
        return [token for token in tokens if len(token) >= 1]

    def _recompute_statistics(self) -> None:
        """Tái tính toán thống kê toàn cục: Document Frequencies, Average Doc Length và IDF."""
        num_docs = len(self._corpus)
        if num_docs == 0:
            self._avgdl = 0.0
            self._doc_frequencies = Counter()
            self._idf = {}
            return

        # Tính Document Frequencies (mỗi từ trong 1 chunk chỉ đếm 1 lần)
        self._doc_frequencies = Counter()
        for tokens in self._tokenized_corpus.values():
            unique_terms = set(tokens)
            self._doc_frequencies.update(unique_terms)

        # Tính Average Document Length (avgdl)
        total_length = sum(self._doc_lengths.values())
        self._avgdl = total_length / num_docs

        # Tính IDF theo công thức chuẩn Lucene / BM25+ smoothing
        # IDF(q_i) = ln((N - DF(q_i) + 0.5) / (DF(q_i) + 0.5) + 1.0)
        self._idf = {}
        for term, df in self._doc_frequencies.items():
            self._idf[term] = math.log(((num_docs - df + 0.5) / (df + 0.5)) + 1.0)

    def index_chunks(self, chunks: Sequence[Chunk]) -> int:
        """Đánh chỉ mục danh sách chunks và cập nhật toàn bộ thống kê BM25.

        Args:
            chunks: Danh sách các đoạn văn bản (Chunks).

        Returns:
            Số lượng chunks đã index thành công.
        """
        if not chunks:
            return 0

        for chunk in chunks:
            tokens = self.tokenize(chunk.text)
            self._corpus[chunk.chunk_id] = chunk
            self._tokenized_corpus[chunk.chunk_id] = tokens
            self._doc_lengths[chunk.chunk_id] = len(tokens)

        self._recompute_statistics()
        return len(chunks)

    def score(self, query_tokens: list[str], chunk_id: str) -> float:
        """Tính điểm BM25 của một chunk cụ thể đối với danh sách query tokens.

        Công thức Okapi BM25:
        Score(D, Q) = sum_{q_i in Q} IDF(q_i) * (TF * (k1 + 1)) / (TF + k1 * (1 - b + b * (|D| / avgdl)))
        """
        if self._avgdl <= 0.0 or chunk_id not in self._tokenized_corpus:
            return 0.0

        doc_tokens = self._tokenized_corpus[chunk_id]
        doc_len = self._doc_lengths[chunk_id]
        term_freqs = Counter(doc_tokens)

        len_norm = 1.0 - self.b + self.b * (doc_len / self._avgdl)
        total_score = 0.0

        for q_i in query_tokens:
            tf = term_freqs.get(q_i, 0)
            if tf == 0:
                continue

            idf = self._idf.get(q_i, 0.0)
            term_score = idf * (tf * (self.k1 + 1.0)) / (tf + self.k1 * len_norm)
            total_score += term_score

        return total_score

    def search(
        self,
        query: str,
        top_k: int = 10,
        document_id: str | None = None,
    ) -> list[SearchResult]:
        """Tìm kiếm từ khóa bằng thuật toán BM25.

        Args:
            query: Chuỗi truy vấn tìm kiếm.
            top_k: Số lượng kết quả nhiều nhất cần lấy.
            document_id: (Tùy chọn) Chỉ tìm trong tài liệu có ID này.

        Returns:
            Danh sách SearchResult sắp xếp theo điểm BM25 giảm dần.
        """
        cleaned_query = query.strip()
        if not cleaned_query or not self._corpus:
            return []

        query_tokens = self.tokenize(cleaned_query)
        if not query_tokens:
            return []

        # Lọc danh sách chunks theo document_id nếu có
        candidate_chunk_ids = [
            cid for cid, chunk in self._corpus.items()
            if document_id is None or chunk.document_id == document_id
        ]

        scored_candidates: list[tuple[str, float]] = []
        for cid in candidate_chunk_ids:
            chunk_score = self.score(query_tokens, cid)
            if chunk_score > 0.0:
                scored_candidates.append((cid, chunk_score))

        # Sắp xếp giảm dần theo điểm BM25
        scored_candidates.sort(key=lambda item: item[1], reverse=True)
        top_candidates = scored_candidates[:top_k]

        results: list[SearchResult] = []
        for cid, sc in top_candidates:
            chunk = self._corpus[cid]
            results.append(
                SearchResult(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    text=chunk.text,
                    page_numbers=chunk.page_numbers,
                    score=sc,
                )
            )

        return results

    def delete_by_document(self, document_id: str) -> int:
        """Xóa toàn bộ chunks của một tài liệu và tính toán lại thống kê BM25.

        Args:
            document_id: Mã định danh tài liệu cần xóa.

        Returns:
            Số lượng chunks đã xóa.
        """
        chunks_to_remove = [
            cid for cid, chunk in self._corpus.items()
            if chunk.document_id == document_id
        ]

        for cid in chunks_to_remove:
            self._corpus.pop(cid, None)
            self._tokenized_corpus.pop(cid, None)
            self._doc_lengths.pop(cid, None)

        if chunks_to_remove:
            self._recompute_statistics()

        return len(chunks_to_remove)

    def clear(self) -> None:
        """Xóa sạch toàn bộ chỉ mục."""
        self._corpus.clear()
        self._tokenized_corpus.clear()
        self._doc_lengths.clear()
        self._avgdl = 0.0
        self._doc_frequencies.clear()
        self._idf.clear()
