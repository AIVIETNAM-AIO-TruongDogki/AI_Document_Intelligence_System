import re
from collections.abc import Sequence
from dataclasses import dataclass

from app.rag.context_builder import CitationSource


@dataclass(frozen=True)
class FaithfulnessResult:
    """Kết quả hậu kiểm độ trung thực (Faithfulness & Hallucination Guardrail)."""

    faithfulness_score: float
    is_verified: bool
    verified_answer: str
    cited_indices: list[int]
    unsupported_claims_removed: int = 0


class FaithfulnessVerifier:
    """Bộ hậu kiểm chứng thực câu trả lời (Post-generation Faithfulness Verifier).

    Đảm bảo:
    1. Mọi trích dẫn `[Nguồn X]` trong câu trả lời đều tồn tại thực sự trong danh sách nguồn.
    2. Các câu khẳng định mang thông tin định lượng/thực thể phải có độ phủ từ vựng (Lexical/Entity Grounding)
       với các đoạn ngữ cảnh đã truy hồi.
    3. Tự động lọc bỏ câu suy đoán ngoài ngữ cảnh hoặc trả về thông báo an toàn nếu điểm trung thực quá thấp.
    """

    def __init__(self, min_faithfulness_score: float = 0.65) -> None:
        self.min_faithfulness_score = min_faithfulness_score

    def _tokenize(self, text: str) -> set[str]:
        clean = re.sub(r"[^\w\s]|_", " ", text.lower())
        stopwords = {
            "là", "của", "và", "các", "trong", "được", "cho", "với", "theo", "tại", "về",
            "những", "một", "này", "đó", "khi", "để", "từ", "đến", "hay", "hoặc", "không",
            "nguồn", "tài", "liệu", "cung", "cấp", "thông", "tin", "quy", "định",
            "the", "is", "are", "of", "and", "in", "to", "for", "with", "on", "a", "an", "by",
        }
        return {t for t in clean.split() if len(t) > 1 and t not in stopwords}

    def verify(
        self,
        answer: str,
        sources: Sequence[CitationSource],
        full_context_text: str = "",
    ) -> FaithfulnessResult:
        """Kiểm chứng câu trả lời của LLM đối với danh sách nguồn trích dẫn."""
        cleaned_answer = answer.strip()
        if not cleaned_answer:
            return FaithfulnessResult(
                faithfulness_score=0.0,
                is_verified=False,
                verified_answer="Thông tin này không được đề cập trong tài liệu được cung cấp.",
                cited_indices=[],
            )

        # Trường hợp hệ thống chủ động từ chối trả lời (Abstain / Fast Reject) -> Trung thực 100%
        if "Thông tin này không được đề cập" in cleaned_answer:
            return FaithfulnessResult(
                faithfulness_score=1.0,
                is_verified=True,
                verified_answer=cleaned_answer,
                cited_indices=[],
            )

        if not sources:
            # Có câu trả lời nhưng không có bất kỳ nguồn nào -> Nguy cơ ảo giác
            return FaithfulnessResult(
                faithfulness_score=0.0,
                is_verified=False,
                verified_answer="Thông tin này không được đề cập trong tài liệu được cung cấp.",
                cited_indices=[],
            )

        valid_source_map = {src.source_index: src for src in sources}
        cited_matches = re.findall(r"\[Nguồn\s+(\d+)\]", cleaned_answer)
        cited_indices = sorted({int(idx) for idx in cited_matches})

        # Kiểm tra xem có trích dẫn khống (ví dụ [Nguồn 9] khi chỉ có 2 nguồn) hay không
        invalid_citations = [idx for idx in cited_indices if idx not in valid_source_map]
        valid_citations = [idx for idx in cited_indices if idx in valid_source_map]

        # Tập hợp toàn bộ từ vựng bằng chứng từ context và snippets
        evidence_corpus = full_context_text + " " + " ".join(s.snippet for s in sources)
        evidence_tokens = self._tokenize(evidence_corpus)

        # Tách câu trả lời thành từng mệnh đề/câu để kiểm tra grounding
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", cleaned_answer) if s.strip()]
        supported_sentences: list[str] = []
        unsupported_count = 0
        sentence_scores: list[float] = []

        for sent in sentences:
            # Xóa trích dẫn khống trong câu nếu có
            for inv_idx in invalid_citations:
                sent = re.sub(rf"\s*\[Nguồn\s+{inv_idx}\]", "", sent)

            sent_without_cite = re.sub(r"\[Nguồn\s+\d+\]", "", sent).strip()
            sent_tokens = self._tokenize(sent_without_cite)

            if not sent_tokens:
                supported_sentences.append(sent)
                sentence_scores.append(1.0)
                continue

            overlap = len(sent_tokens & evidence_tokens) / len(sent_tokens)
            has_valid_cite = bool(re.search(r"\[Nguồn\s+\d+\]", sent))

            # Điểm grounding của câu kết hợp giữa overlap từ vựng và trích dẫn hợp lệ
            sent_score = min(1.0, overlap * 1.45 + (0.25 if has_valid_cite else 0.0))

            if sent_score >= 0.35:
                supported_sentences.append(sent)
                sentence_scores.append(sent_score)
            else:
                unsupported_count += 1
                sentence_scores.append(0.1)

        raw_score = sum(sentence_scores) / len(sentence_scores) if sentence_scores else 0.0
        if invalid_citations:
            raw_score *= 0.6

        final_score = round(min(max(raw_score, 0.0), 1.0), 4)
        is_verified = final_score >= self.min_faithfulness_score and len(supported_sentences) > 0

        if is_verified:
            verified_text = " ".join(supported_sentences)
            # Nếu câu trả lời đúng trọng tâm nhưng LLM quên gắn tag [Nguồn 1], tự động bổ sung nguồn chính
            if not valid_citations and sources:
                primary_idx = sources[0].source_index
                verified_text = f"{verified_text} [Nguồn {primary_idx}]"
                valid_citations = [primary_idx]
        else:
            verified_text = (
                "Cảnh báo: Không đủ căn cứ chắc chắn trong tài liệu để kết luận chính xác cho câu hỏi này."
            )

        return FaithfulnessResult(
            faithfulness_score=final_score,
            is_verified=is_verified,
            verified_answer=verified_text,
            cited_indices=valid_citations,
            unsupported_claims_removed=unsupported_count,
        )

