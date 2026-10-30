from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum

from app.retrieval.models import SearchResult


class GatekeeperDecision(str, Enum):
    """Quyết định điều hướng của Probability Gatekeeper (CRAG)."""

    ACCEPT = "ACCEPT"            # P >= 0.70: Độ tin cậy cao -> Chuyển thẳng tới LLM
    REWRITE = "REWRITE"          # 0.35 <= P < 0.70: Mơ hồ -> Kích hoạt Query Rewriter & truy hồi lần 2
    FAST_REJECT = "FAST_REJECT"  # P < 0.35: Ngoài phạm vi -> Từ chối ngay (< 50ms, 0 LLM tokens)


@dataclass(frozen=True)
class GatekeeperEvaluation:
    """Kết quả đánh giá xác suất liên quan tại tầng biên."""

    decision: GatekeeperDecision
    max_probability: float
    filtered_results: list[SearchResult]
    reason: str


class RAGGatekeeper:
    """Bộ gác cổng xác suất (Probability Gatekeeper) cho Corrective RAG (CRAG).

    Đánh giá phân phối điểm xác suất P(relevance) từ Cross-Encoder Reranker để:
    1. Chặn sớm (Fast Reject) các câu hỏi ngoài lề (Out-of-Domain) mà không tốn chi phí gọi LLM.
    2. Phát hiện các truy vấn mơ hồ (Ambiguous) để kích hoạt luồng tự sửa lỗi (Query Rewriting).
    3. Chỉ cho phép các ngữ cảnh có độ tin cậy cao đi vào bước sinh câu trả lời.
    """

    def __init__(
        self,
        accept_threshold: float = 0.70,
        reject_threshold: float = 0.35,
    ) -> None:
        if not (0.0 <= reject_threshold < accept_threshold <= 1.0):
            raise ValueError("Ngưỡng phải thỏa mãn: 0.0 <= reject_threshold < accept_threshold <= 1.0")
        self.accept_threshold = accept_threshold
        self.reject_threshold = reject_threshold

    def evaluate(self, search_results: Sequence[SearchResult]) -> GatekeeperEvaluation:
        """Phân tích danh sách kết quả đã qua Reranker và đưa ra quyết định điều hướng."""
        if not search_results:
            return GatekeeperEvaluation(
                decision=GatekeeperDecision.FAST_REJECT,
                max_probability=0.0,
                filtered_results=[],
                reason="Không tìm thấy đoạn văn bản nào trong kho dữ liệu.",
            )

        max_prob = max(r.score for r in search_results)

        if max_prob < self.reject_threshold:
            return GatekeeperEvaluation(
                decision=GatekeeperDecision.FAST_REJECT,
                max_probability=round(max_prob, 4),
                filtered_results=[],
                reason=f"Xác suất liên quan cao nhất ({max_prob:.2f}) thấp hơn ngưỡng chặn ({self.reject_threshold:.2f}).",
            )

        # Giữ lại các đoạn có xác suất >= reject_threshold để tránh đưa nhiễu vào Context
        valid_results = [r for r in search_results if r.score >= self.reject_threshold]

        if max_prob < self.accept_threshold:
            return GatekeeperEvaluation(
                decision=GatekeeperDecision.REWRITE,
                max_probability=round(max_prob, 4),
                filtered_results=valid_results,
                reason=(
                    f"Xác suất liên quan ở mức trung bình ({max_prob:.2f} in "
                    f"[{self.reject_threshold:.2f}, {self.accept_threshold:.2f})), cần mở rộng truy vấn."
                ),
            )

        return GatekeeperEvaluation(
            decision=GatekeeperDecision.ACCEPT,
            max_probability=round(max_prob, 4),
            filtered_results=valid_results,
            reason=f"Độ tin cậy ngữ cảnh đạt chuẩn ({max_prob:.2f} >= {self.accept_threshold:.2f}).",
        )

