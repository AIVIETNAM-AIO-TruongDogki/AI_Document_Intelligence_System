import re
from dataclasses import dataclass

from app.llm.base import BaseLLMProvider, LLMRequest

# Từ điển mở rộng từ đồng nghĩa & thuật ngữ chuyên ngành phổ biến (Zero-latency Domain Dictionary)
DOMAIN_SYNONYM_MAP: dict[str, str] = {
    "nghỉ việc": "chấm dứt hợp đồng lao động thôi việc nghỉ phép",
    "xin nghỉ": "quy định nghỉ phép nghỉ ốm hưởng lương",
    "ngày nghỉ": "nghỉ phép hàng năm ngày phép",
    "tiền lương": "chính sách lương thưởng phụ cấp thu nhập",
    "bảo hiểm": "bảo hiểm y tế bảo hiểm xã hội chế độ ốm đau",
    "chậm trễ": "độ trễ latency thời gian phản hồi",
    "ảo giác": "hallucination bịa đặt thông tin faithfulness",
    "tìm kiếm": "truy hồi retrieval hybrid search vector bm25",
    "mô hình hình ảnh": "vision language model vlm image quality assessment",
    "tối ưu chính sách": "group relative policy optimization grpo ppo reinforcement learning",
    "chất lượng ảnh": "image quality assessment q-insight aesthetic reasoning",
    "bất thường video": "video anomaly reasoning vad-r1 chain of thought",
}


@dataclass(frozen=True)
class RewriteResult:
    original_query: str
    rewritten_query: str
    used_llm: bool
    tokens_used: int = 0


class QueryRewriter:
    """Module tái diễn đạt và mở rộng truy vấn (Adaptive Query Rewriter) cho CRAG.

    Khi Gatekeeper phát hiện điểm liên quan ở vùng mơ hồ (0.35 <= P < 0.70),
    QueryRewriter kết hợp từ điển thuật ngữ chuyên ngành và LLM (nếu cần) để
    bổ sung từ khóa chuẩn xác trước khi truy hồi lần 2.
    """

    def __init__(
        self,
        llm_provider: BaseLLMProvider | None = None,
        use_llm_expansion: bool = False,
    ) -> None:
        self.llm_provider = llm_provider
        self.use_llm_expansion = use_llm_expansion

    def rewrite(self, query: str) -> RewriteResult:
        """Mở rộng câu hỏi mơ hồ thành truy vấn giàu từ khóa chuyên ngành."""
        cleaned = query.strip()
        if not cleaned:
            return RewriteResult(original_query=query, rewritten_query=query, used_llm=False)

        lower_q = cleaned.lower()
        expanded_terms: list[str] = []

        for phrase, expansion in DOMAIN_SYNONYM_MAP.items():
            if phrase in lower_q:
                expanded_terms.append(expansion)

        # Nếu có cấu hình gọi LLM expansion và không phải MockLLM
        if self.use_llm_expansion and self.llm_provider is not None:
            prompt = (
                "Hãy viết lại câu hỏi sau bằng cách bổ sung các thuật ngữ chuyên môn và từ khóa đồng nghĩa "
                "ngắn gọn để phục vụ tìm kiếm tài liệu (chỉ trả về câu truy vấn mới trên 1 dòng):\n"
                f"Câu hỏi gốc: {cleaned}"
            )
            resp = self.llm_provider.generate(
                LLMRequest(prompt=prompt, temperature=0.0, max_tokens=128)
            )
            candidate = resp.content.strip()
            if candidate and not candidate.startswith("Mock answer"):
                return RewriteResult(
                    original_query=cleaned,
                    rewritten_query=f"{cleaned} {candidate}",
                    used_llm=True,
                    tokens_used=resp.prompt_tokens + resp.completion_tokens,
                )

        if expanded_terms:
            rewritten = f"{cleaned} {' '.join(expanded_terms)}"
        else:
            # Trích xuất các từ khóa cốt lõi (loại bỏ từ để hỏi) để tăng trọng số BM25/Dense
            core_words = [
                w
                for w in re.sub(r"[^\w\s]", " ", lower_q).split()
                if w not in {"là", "gì", "như", "thế", "nào", "ở", "đâu", "bao", "nhiêu", "có", "không"}
            ]
            rewritten = f"{cleaned} {' '.join(core_words)}" if core_words else cleaned

        return RewriteResult(
            original_query=cleaned,
            rewritten_query=rewritten.strip(),
            used_llm=False,
            tokens_used=0,
        )

