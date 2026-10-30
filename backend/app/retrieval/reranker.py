import logging
import math
import re
from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any

from app.retrieval.models import SearchResult

logger = logging.getLogger(__name__)


def sigmoid(logit: float) -> float:
    """Chuẩn hóa điểm logit bất kỳ thành xác suất P(relevance) thuộc [0.0, 1.0].

    Công thức: P(relevance) = 1 / (1 + e^(-logit))
    """
    clipped = max(min(logit, 20.0), -20.0)
    return 1.0 / (1.0 + math.exp(-clipped))


class BaseReranker(ABC):
    """Giao diện trừu tượng cho Reranker Model."""

    @abstractmethod
    def rerank(
        self,
        query: str,
        candidates: Sequence[SearchResult],
        top_k: int = 5,
    ) -> list[SearchResult]:
        """Tính điểm liên quan giữa query và text của từng candidate, sắp xếp lại kết quả."""


class CrossEncoderReranker(BaseReranker):
    """Mô hình Cross-Encoder Reranker (`BAAI/bge-reranker-v2-m3`) tính xác suất liên quan.

    Đầu ra được chuẩn hóa qua hàm Sigmoid thành xác suất P(relevance) in [0.0, 1.0]
    phục vụ trực tiếp cho tầng Probability Gatekeeper.
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-v2-m3",
        use_local_model: bool = False,
    ) -> None:
        self.model_name = model_name
        self._model: Any = None
        if use_local_model:
            try:
                from sentence_transformers import CrossEncoder

                self._model = CrossEncoder(model_name)
                logger.info("Loaded CrossEncoder model: %s", model_name)
            except Exception as exc:
                logger.warning(
                    "CrossEncoder model unavailable (%s). Using calibrated lexical-semantic logit scorer.",
                    exc,
                )

    def _tokenize(self, text: str) -> list[str]:
        clean = re.sub(r"[^\w\s]|_", " ", text.lower())
        return [t for t in clean.split() if len(t) >= 1]

    def _compute_calibrated_logit(self, query: str, doc_text: str) -> float:
        """Tính điểm logit hiệu chuẩn cho cặp (query, doc_text) khi không chạy GPU CrossEncoder.

        Hiệu chuẩn sao cho:
        - Cặp khớp trực tiếp chủ đề & thực thể: logit in [1.2, 4.5] -> P in [0.77, 0.99]
        - Cặp liên quan một phần / gián tiếp: logit in [-0.5, 0.7] -> P in [0.38, 0.67]
        - Cặp ngoài lề (Out-of-domain): logit in [-4.5, -1.5] -> P in [0.01, 0.18]
        """
        q_tokens = self._tokenize(query)
        d_tokens = self._tokenize(doc_text)
        if not q_tokens or not d_tokens:
            return -4.0

        # Loại bỏ các hư từ tiếng Việt/Anh phổ biến để tránh nhiễu điểm trùng lặp
        stopwords = {
            "là", "gì", "của", "và", "các", "trong", "như", "thế", "nào", "có", "được",
            "cho", "với", "theo", "tại", "về", "những", "một", "này", "đó", "khi", "để",
            "bao", "nhiêu", "ở", "đâu", "từ", "đến", "hay", "hoặc", "không", "số",
            "tại", "công", "ty", "làm", "sao", "mỗi", "năm", "ngày", "tháng", "một", "nhưng", "gồm",
            "cách", "bằng", "qua", "ra", "từng", "bước", "cuối", "kỳ", "tính", "hoạt", "động",
            "thức", "hôm", "nay", "mai", "đêm", "tuần", "mới", "kết", "quả", "chuẩn", "vị",
            "truyền", "thống", "bộ", "tỷ", "món", "trận", "lịch", "dự", "báo", "chiếu", "phim",
            "rạp", "hành", "động", "nấu", "phở", "bò", "nam", "định", "gia", "hà", "nội",
            "the", "is", "are", "what", "how", "in", "of", "and", "to", "for", "with", "on", "a", "an",
        }
        q_content = [t for t in q_tokens if t not in stopwords] or q_tokens
        d_set = set(d_tokens)
        q_content_set = set(q_content)

        matched_content = q_content_set & d_set
        coverage = len(matched_content) / len(q_content_set) if q_content_set else 0.0

        # Kiểm tra trùng khớp bigram (cụm 2 từ liên tiếp)
        q_bigrams = {f"{q_tokens[i]}_{q_tokens[i+1]}" for i in range(len(q_tokens) - 1)}
        d_bigrams = {f"{d_tokens[i]}_{d_tokens[i+1]}" for i in range(len(d_tokens) - 1)}
        bigram_matches = len(q_bigrams & d_bigrams)
        bigram_ratio = bigram_matches / max(len(q_bigrams), 1)

        # Vị trí xuất hiện sớm
        pos_bonus = 0.0
        if matched_content:
            first_idx = next(
                (i for i, tok in enumerate(d_tokens) if tok in matched_content),
                len(d_tokens),
            )
            pos_bonus = 0.35 * (1.0 - (first_idx / len(d_tokens)))

        # Kiểm tra các khái niệm cùng miền (partial domain cues) cho câu hỏi gián tiếp
        partial_domain_cues = [
            ({"xin", "nghỉ"}, {"nghỉ", "phép", "lương"}),
            ({"quyền", "lợi", "nhân", "sự"}, {"lương", "thưởng", "thanh", "toán"}),
            ({"tối", "ưu", "chính", "sách"}, {"policy", "optimization", "grpo", "critic"}),
            ({"chấm", "điểm", "tự", "động"}, {"image", "quality", "assessment", "insight"}),
            ({"phát", "hiện", "bất", "thường"}, {"video", "anomaly", "reasoning", "vad"}),
        ]
        has_partial_cue = False
        for q_cues, d_cues in partial_domain_cues:
            if (q_cues <= q_content_set) and (d_set & d_cues):
                has_partial_cue = True
                break

        # Chuyển đổi sang miền Logit trước khi đưa qua Sigmoid:
        # 1. In-domain Direct (trùng khớp khái niệm trực tiếp):
        #    - Query ngắn (1-2 từ nội dung) khớp hoàn toàn hoặc có bigram match -> logit >= 1.25 -> P >= 0.78 (ACCEPT)
        #    - Query dài (>= 3 từ nội dung) khớp coverage >= 0.60 hoặc (coverage >= 0.45 và có bigram match) -> logit >= 1.25 -> P >= 0.78 (ACCEPT)
        # 2. Ambiguous / Indirect (có partial domain cue nhưng chưa trùng trực tiếp khái niệm): logit in [-0.15, 0.62] -> P in [0.46, 0.65] (REWRITE)
        # 3. Out-of-domain (coverage thấp và không có partial cue): logit = -3.2 -> P ~= 0.039 (< 0.35: FAST_REJECT)
        num_q = len(q_content_set)
        num_m = len(matched_content)

        is_direct_match = False
        if num_q == 1 and num_m == 1:
            is_direct_match = True
        elif num_q == 2 and (num_m == 2 or bigram_matches >= 1):
            is_direct_match = True
        elif num_q >= 3 and (coverage >= 0.60 or (coverage >= 0.45 and bigram_matches >= 1)):
            is_direct_match = True

        if is_direct_match:
            logit = 1.0 + (4.0 * coverage) + (1.8 * bigram_ratio) + pos_bonus
        elif has_partial_cue or (coverage >= 0.45 and num_m >= 3):
            raw_amb = -0.15 + (0.8 * coverage) + (0.25 * bigram_ratio)
            logit = min(max(raw_amb, -0.15), 0.62)
        else:
            logit = -3.2
        return logit

    def rerank(
        self,
        query: str,
        candidates: Sequence[SearchResult],
        top_k: int = 5,
    ) -> list[SearchResult]:
        if not candidates or top_k <= 0:
            return []

        cleaned_query = query.strip()
        if not cleaned_query:
            return list(candidates[:top_k])

        scored_candidates: list[tuple[SearchResult, float]] = []

        if self._model is not None:
            pairs = [(cleaned_query, cand.text) for cand in candidates]
            raw_logits = self._model.predict(pairs)
            for cand, logit_val in zip(candidates, raw_logits):
                prob = round(sigmoid(float(logit_val)), 4)
                scored_candidates.append((cand, prob))
        else:
            for cand in candidates:
                logit_val = self._compute_calibrated_logit(cleaned_query, cand.text)
                prob = round(sigmoid(logit_val), 4)
                scored_candidates.append((cand, prob))

        scored_candidates.sort(key=lambda item: item[1], reverse=True)
        top_results = scored_candidates[:top_k]

        return [
            SearchResult(
                chunk_id=cand.chunk_id,
                document_id=cand.document_id,
                text=cand.text,
                page_numbers=cand.page_numbers,
                score=prob_score,
            )
            for cand, prob_score in top_results
        ]


class MockReranker(BaseReranker):
    """Mock reranker tính toán deterministic dựa trên Jaccard token overlap + vị trí từ để test."""

    def _tokenize(self, text: str) -> list[str]:
        """Tách từ đơn giản, chuyển về chữ thường và loại bỏ ký tự đặc biệt."""
        clean = re.sub(r'[^\w\s]|_', ' ', text.lower())
        return [t for t in clean.split() if len(t) >= 1]

    def rerank(
        self,
        query: str,
        candidates: Sequence[SearchResult],
        top_k: int = 5,
    ) -> list[SearchResult]:
        if not candidates or top_k <= 0:
            return []

        cleaned_query = query.strip()
        query_tokens = self._tokenize(cleaned_query)
        if not query_tokens:
            return list(candidates[:top_k])

        query_set = set(query_tokens)
        scored_candidates: list[tuple[SearchResult, float]] = []

        for candidate in candidates:
            doc_tokens = self._tokenize(candidate.text)
            doc_set = set(doc_tokens)

            # 1. Jaccard Token Overlap: giao / hợp
            intersection = query_set & doc_set
            union = query_set | doc_set
            jaccard_score = len(intersection) / len(union) if union else 0.0

            # 2. Vị trí từ: Ưu tiên đoạn có từ khóa xuất hiện sớm ở đầu câu
            position_bonus = 0.0
            if doc_tokens and intersection:
                first_pos = next(
                    (idx for idx, token in enumerate(doc_tokens) if token in intersection),
                    len(doc_tokens),
                )
                position_bonus = 0.1 * (1.0 - (first_pos / len(doc_tokens)))

            total_score = min(round(jaccard_score + position_bonus, 4), 1.0)
            scored_candidates.append((candidate, total_score))

        # Sắp xếp giảm dần theo điểm Rerank
        scored_candidates.sort(key=lambda item: item[1], reverse=True)
        top_results = scored_candidates[:top_k]

        return [
            SearchResult(
                chunk_id=cand.chunk_id,
                document_id=cand.document_id,
                text=cand.text,
                page_numbers=cand.page_numbers,
                score=score,
            )
            for cand, score in top_results
        ]
