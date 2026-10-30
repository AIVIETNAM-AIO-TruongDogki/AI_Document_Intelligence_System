import time
from dataclasses import dataclass, field

from app.core.observability import observe, observer
from app.llm.base import BaseLLMProvider, LLMRequest
from app.rag.context_builder import CitationSource, ContextBuilder
from app.rag.gatekeeper import GatekeeperDecision, RAGGatekeeper
from app.rag.prompt import RAG_SYSTEM_INSTRUCTION, format_rag_prompt
from app.rag.rewriter import QueryRewriter
from app.rag.verifier import FaithfulnessVerifier
from app.retrieval.service import HybridSearchService

FAST_REJECT_MESSAGE = "Thông tin này không được đề cập trong tài liệu được cung cấp."


@dataclass(frozen=True)
class RAGAnswer:
    answer: str
    sources: list[CitationSource]
    model_name: str
    tokens_used: dict[str, int]
    faithfulness_score: float = 1.0
    is_verified: bool = True
    gatekeeper_decision: str = "ACCEPT"
    relevance_probability: float = 1.0
    rewritten_query: str | None = None
    latency_ms: float = 0.0
    trace_metadata: dict[str, object] = field(default_factory=dict)


class RAGService:
    """Service điều phối toàn diện cho quy trình Corrective RAG (Enterprise Self-Correcting RAG).

    Hỗ trợ:
    1. Hybrid Retrieval (Dense + BM25 + RRF + Cross-Encoder Rerank).
    2. Probability Gatekeeper:
       - FAST_REJECT (P < 0.35): Chặn ngay câu hỏi ngoài lề (< 50ms, 0 LLM tokens).
       - REWRITE (0.35 <= P < 0.70): Mở rộng truy vấn qua QueryRewriter & truy hồi lần 2.
       - ACCEPT (P >= 0.70): Chuyển thẳng vào ContextBuilder & LLM.
    3. Post-generation Faithfulness Verifier: Hậu kiểm chống ảo giác 100%.
    4. Langfuse Distributed Tracing: Giám sát từng bước qua `@observe()`.
    """

    def __init__(
        self,
        retrieval_service: HybridSearchService,
        context_builder: ContextBuilder,
        llm_provider: BaseLLMProvider,
        gatekeeper: RAGGatekeeper | None = None,
        query_rewriter: QueryRewriter | None = None,
        faithfulness_verifier: FaithfulnessVerifier | None = None,
        enable_gatekeeper: bool = False,
        enable_verifier: bool = True,
    ) -> None:
        self.retrieval_service = retrieval_service
        self.context_builder = context_builder
        self.llm_provider = llm_provider
        self.gatekeeper = gatekeeper or RAGGatekeeper()
        self.query_rewriter = query_rewriter or QueryRewriter(llm_provider=llm_provider)
        self.faithfulness_verifier = faithfulness_verifier or FaithfulnessVerifier()
        self.enable_gatekeeper = enable_gatekeeper
        self.enable_verifier = enable_verifier

    @observe(name="RAGService.answer_question")
    def answer_question(
        self,
        query: str,
        document_id: str | None = None,
        top_k: int = 5,
    ) -> RAGAnswer:
        """Thực thi pipeline CRAG từ đầu đến cuối và trả về câu trả lời kèm bằng chứng đã hậu kiểm."""
        t_start = time.perf_counter()
        cleaned_query = query.strip()
        if not cleaned_query:
            raise ValueError("Câu hỏi không được để trống.")

        model_name = getattr(self.llm_provider, "model_name", self.llm_provider.__class__.__name__)

        # Bước 1: Truy hồi ứng viên lần 1 qua Hybrid Search
        search_results = self.retrieval_service.search(
            query=cleaned_query,
            top_k=top_k,
            document_id=document_id,
        )

        gatekeeper_decision = GatekeeperDecision.ACCEPT
        max_prob = max((r.score for r in search_results), default=0.0)
        rewritten_query_str: str | None = None
        rewrite_tokens = 0

        # Bước 2: Đánh giá qua Probability Gatekeeper & Adaptive Routing (CRAG)
        if self.enable_gatekeeper:
            gk_eval = self.gatekeeper.evaluate(search_results)
            gatekeeper_decision = gk_eval.decision
            max_prob = gk_eval.max_probability

            if gatekeeper_decision == GatekeeperDecision.FAST_REJECT:
                elapsed_ms = (time.perf_counter() - t_start) * 1000.0
                trace = observer.finalize_trace(
                    name="rag_fast_reject",
                    total_latency_ms=elapsed_ms,
                    metadata={
                        "query": cleaned_query,
                        "decision": gatekeeper_decision.value,
                        "probability": max_prob,
                    },
                )
                return RAGAnswer(
                    answer=FAST_REJECT_MESSAGE,
                    sources=[],
                    model_name="gatekeeper-fast-reject",
                    tokens_used={
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0,
                    },
                    faithfulness_score=1.0,
                    is_verified=True,
                    gatekeeper_decision=gatekeeper_decision.value,
                    relevance_probability=max_prob,
                    rewritten_query=None,
                    latency_ms=round(elapsed_ms, 2),
                    trace_metadata={"trace_id": trace.trace_id, "reason": gk_eval.reason},
                )

            if gatekeeper_decision == GatekeeperDecision.REWRITE:
                rewrite_res = self.query_rewriter.rewrite(cleaned_query)
                rewritten_query_str = rewrite_res.rewritten_query
                rewrite_tokens = rewrite_res.tokens_used

                # Truy hồi lần 2 (1 lần duy nhất theo kiến trúc CRAG)
                retry_results = self.retrieval_service.search(
                    query=rewritten_query_str,
                    top_k=top_k,
                    document_id=document_id,
                )
                retry_eval = self.gatekeeper.evaluate(retry_results)
                if retry_eval.max_probability >= max_prob:
                    search_results = retry_eval.filtered_results or retry_results
                    max_prob = retry_eval.max_probability
                else:
                    search_results = gk_eval.filtered_results

                # Nếu sau khi rewrite vẫn dưới ngưỡng reject thì từ chối an toàn
                if max_prob < self.gatekeeper.reject_threshold:
                    elapsed_ms = (time.perf_counter() - t_start) * 1000.0
                    trace = observer.finalize_trace(
                        name="rag_rewrite_reject",
                        total_latency_ms=elapsed_ms,
                        metadata={
                            "query": cleaned_query,
                            "rewritten_query": rewritten_query_str,
                            "decision": GatekeeperDecision.FAST_REJECT.value,
                            "probability": max_prob,
                        },
                    )
                    return RAGAnswer(
                        answer=FAST_REJECT_MESSAGE,
                        sources=[],
                        model_name="gatekeeper-fast-reject",
                        tokens_used={
                            "prompt_tokens": rewrite_tokens,
                            "completion_tokens": 0,
                            "total_tokens": rewrite_tokens,
                        },
                        faithfulness_score=1.0,
                        is_verified=True,
                        gatekeeper_decision=GatekeeperDecision.FAST_REJECT.value,
                        relevance_probability=max_prob,
                        rewritten_query=rewritten_query_str,
                        latency_ms=round(elapsed_ms, 2),
                        trace_metadata={"trace_id": trace.trace_id},
                    )
            else:
                search_results = gk_eval.filtered_results

        # Bước 3: Xây dựng khối ngữ cảnh và danh sách nguồn theo ngân sách token
        built_context = self.context_builder.build(search_results)

        # Bước 4: Ráp ngữ cảnh và câu hỏi vào khung prompt chuẩn chống ảo giác
        rag_prompt = format_rag_prompt(
            query=cleaned_query,
            context_text=built_context.context_text,
        )

        # Bước 5: Gửi yêu cầu tới LLM Engine
        llm_request = LLMRequest(
            prompt=rag_prompt,
            system_instruction=RAG_SYSTEM_INSTRUCTION,
            temperature=0.0,
            max_tokens=1024,
        )
        llm_response = self.llm_provider.generate(llm_request)

        final_answer = llm_response.content
        faithfulness_score = 1.0
        is_verified = True

        # Bước 6: Hậu kiểm chứng thực (Faithfulness & Hallucination Guardrail)
        if self.enable_verifier and built_context.sources:
            verification = self.faithfulness_verifier.verify(
                answer=final_answer,
                sources=built_context.sources,
                full_context_text=built_context.context_text,
            )
            faithfulness_score = verification.faithfulness_score
            is_verified = verification.is_verified
            if is_verified:
                final_answer = verification.verified_answer

        prompt_tok = llm_response.prompt_tokens + rewrite_tokens
        comp_tok = llm_response.completion_tokens
        tokens_used = {
            "prompt_tokens": prompt_tok,
            "completion_tokens": comp_tok,
            "total_tokens": prompt_tok + comp_tok,
        }

        elapsed_ms = (time.perf_counter() - t_start) * 1000.0
        trace = observer.finalize_trace(
            name="rag_answer_question",
            total_latency_ms=elapsed_ms,
            metadata={
                "query": cleaned_query,
                "rewritten_query": rewritten_query_str,
                "decision": gatekeeper_decision.value,
                "probability": max_prob,
                "faithfulness_score": faithfulness_score,
                "is_verified": is_verified,
                "tokens_used": tokens_used,
            },
        )

        return RAGAnswer(
            answer=final_answer,
            sources=built_context.sources,
            model_name=model_name,
            tokens_used=tokens_used,
            faithfulness_score=faithfulness_score,
            is_verified=is_verified,
            gatekeeper_decision=gatekeeper_decision.value,
            relevance_probability=round(max_prob, 4),
            rewritten_query=rewritten_query_str,
            latency_ms=round(elapsed_ms, 2),
            trace_metadata={"trace_id": trace.trace_id},
        )
