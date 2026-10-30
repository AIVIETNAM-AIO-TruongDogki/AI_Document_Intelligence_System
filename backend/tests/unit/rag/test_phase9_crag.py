import pytest

from app.documents.models import Chunk
from app.embeddings.bge import BGEM3EmbeddingProvider
from app.embeddings.service import EmbeddingService
from app.llm.base import MockLLMProvider
from app.rag.context_builder import CitationSource, ContextBuilder
from app.rag.gatekeeper import GatekeeperDecision, RAGGatekeeper
from app.rag.rewriter import QueryRewriter
from app.rag.service import FAST_REJECT_MESSAGE, RAGService
from app.rag.verifier import FaithfulnessVerifier
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.models import SearchResult
from app.retrieval.qdrant_store import QdrantVectorStore
from app.retrieval.reranker import CrossEncoderReranker, sigmoid
from app.retrieval.service import HybridSearchService


def test_bge_m3_embedding_dimension_and_similarity() -> None:
    provider = BGEM3EmbeddingProvider(dimension=1024)
    assert provider.dimension == 1024

    v_hr1 = provider.embed_query("Quy định nghỉ phép hàng năm của nhân viên")
    v_hr2 = provider.embed_query("Chính sách nghỉ phép hàng năm cho nhân viên")
    v_ood = provider.embed_query("Giá vàng SJC hôm nay bao nhiêu")

    assert len(v_hr1) == 1024
    sim_related = sum(a * b for a, b in zip(v_hr1, v_hr2))
    sim_ood = sum(a * b for a, b in zip(v_hr1, v_ood))
    assert sim_related > sim_ood


def test_cross_encoder_reranker_and_gatekeeper_decisions() -> None:
    assert round(sigmoid(0.0), 4) == 0.5
    reranker = CrossEncoderReranker()
    gatekeeper = RAGGatekeeper(accept_threshold=0.70, reject_threshold=0.35)

    candidates = [
        SearchResult(
            chunk_id="c1",
            document_id="d1",
            text="Quy định nghỉ phép hàng năm: Mỗi nhân viên được hưởng 14 ngày nghỉ phép.",
            page_numbers=(1,),
            score=0.5,
        )
    ]

    # 1. In-domain query -> ACCEPT (P >= 0.70)
    reranked_accept = reranker.rerank("Quy định nghỉ phép hàng năm bao nhiêu ngày?", candidates)
    eval_accept = gatekeeper.evaluate(reranked_accept)
    assert eval_accept.decision == GatekeeperDecision.ACCEPT
    assert eval_accept.max_probability >= 0.70

    # 2. Out-of-domain query -> FAST_REJECT (P < 0.35)
    reranked_reject = reranker.rerank("Giá vàng SJC hôm nay bao nhiêu?", candidates)
    eval_reject = gatekeeper.evaluate(reranked_reject)
    assert eval_reject.decision == GatekeeperDecision.FAST_REJECT
    assert eval_reject.max_probability < 0.35

    # 3. Short concept query (1-2 keywords) -> ACCEPT (P >= 0.70)
    vad_candidates = [
        SearchResult(
            chunk_id="c_vad",
            document_id="d_vad",
            text="Vad-R1: Towards Video Anomaly Reasoning via Perception-to-Cognition Chain-of-Thought",
            page_numbers=(1,),
            score=0.6,
        )
    ]
    reranked_short = reranker.rerank("Vad-r1 là gì", vad_candidates)
    eval_short = gatekeeper.evaluate(reranked_short)
    assert eval_short.decision == GatekeeperDecision.ACCEPT
    assert eval_short.max_probability >= 0.70


def test_faithfulness_verifier_catches_hallucinations() -> None:
    verifier = FaithfulnessVerifier(min_faithfulness_score=0.65)
    sources = [
        CitationSource(
            source_index=1,
            chunk_id="c1",
            document_id="d1",
            page_numbers=(3,),
            snippet="Quy định nghỉ phép: Nhân viên chính thức được hưởng 14 ngày nghỉ phép mỗi năm.",
        )
    ]

    # Câu trả lời trung thực có trích dẫn hợp lệ
    good_res = verifier.verify(
        answer="Nhân viên chính thức được hưởng 14 ngày nghỉ phép mỗi năm [Nguồn 1].",
        sources=sources,
    )
    assert good_res.is_verified is True
    assert good_res.faithfulness_score >= 0.80
    assert good_res.cited_indices == [1]

    # Câu trả lời bịa đặt trích dẫn khống [Nguồn 9] và nội dung ngoài lề
    bad_res = verifier.verify(
        answer="Công ty tặng mỗi người 1 chiếc xe hơi [Nguồn 9].",
        sources=sources,
    )
    assert bad_res.is_verified is False
    assert bad_res.faithfulness_score < 0.65


def test_crag_service_fast_reject_and_rewrite_flow() -> None:
    emb_service = EmbeddingService(BGEM3EmbeddingProvider(dimension=1024))
    vector_store = QdrantVectorStore(in_memory=True, vector_size=1024)
    bm25 = BM25Retriever()
    reranker = CrossEncoderReranker()

    hybrid = HybridSearchService(
        embedding_service=emb_service,
        vector_store=vector_store,
        bm25_retriever=bm25,
        reranker=reranker,
    )
    hybrid.index_chunks(
        [
            Chunk(
                chunk_id="c_hr",
                document_id="doc_1",
                text="Quy định nghỉ phép hàng năm: Nhân viên được hưởng 14 ngày nghỉ phép nguyên lương.",
                page_numbers=(2,),
                token_count=20,
            )
        ]
    )

    llm = MockLLMProvider(
        fixed_answer="Nhân viên được hưởng 14 ngày nghỉ phép nguyên lương theo quy định [Nguồn 1]."
    )
    rag_service = RAGService(
        retrieval_service=hybrid,
        context_builder=ContextBuilder(),
        llm_provider=llm,
        gatekeeper=RAGGatekeeper(accept_threshold=0.70, reject_threshold=0.35),
        query_rewriter=QueryRewriter(llm_provider=llm),
        faithfulness_verifier=FaithfulnessVerifier(),
        enable_gatekeeper=True,
        enable_verifier=True,
    )

    # 1. Câu hỏi ngoài lề -> Fast Reject, 0 tokens
    ood_ans = rag_service.answer_question("Giá vàng hôm nay bao nhiêu?")
    assert ood_ans.gatekeeper_decision == "FAST_REJECT"
    assert ood_ans.answer == FAST_REJECT_MESSAGE
    assert ood_ans.tokens_used["total_tokens"] == 0
    assert ood_ans.sources == []

    # 2. Câu hỏi mơ hồ ("xin nghỉ") -> Kích hoạt QueryRewriter -> Lấy đúng nguồn
    amb_ans = rag_service.answer_question("Làm sao để xin nghỉ tại công ty?")
    assert amb_ans.rewritten_query is not None
    assert "nghỉ phép" in amb_ans.rewritten_query
    assert len(amb_ans.sources) == 1
    assert amb_ans.is_verified is True

