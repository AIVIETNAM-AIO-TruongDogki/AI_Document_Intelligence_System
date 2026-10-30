from pathlib import Path
import pytest

from app.documents.service import process_pdf
from app.embeddings.gemini import GeminiEmbeddingProvider
from app.embeddings.service import EmbeddingService
from app.llm.gemini import GeminiProvider
from app.rag.context_builder import ContextBuilder
from app.rag.service import RAGService
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.reranker import MockReranker
from app.retrieval.service import HybridSearchService
from app.retrieval.vector_store import InMemoryVectorStore
from app.core.config import settings

def find_raw_data_dir() -> Path:
    candidates = [
        Path("raw_data"),
        Path("../raw_data"),
        Path(__file__).resolve().parents[3] / "raw_data",
        Path(__file__).resolve().parents[2] / "raw_data",
    ]
    for c in candidates:
        if c.is_dir() and list(c.glob("*.pdf")):
            return c
    raise FileNotFoundError("Không tìm thấy thư mục raw_data chứa các tệp PDF.")


RAW_DATA_DIR = find_raw_data_dir()
ALL_PDF_FILES = sorted(list(RAW_DATA_DIR.glob("*.pdf")), key=lambda p: p.stat().st_size)


def test_raw_data_files_exist() -> None:
    """Kiểm tra xem thư mục raw_data có chứa ít nhất 1 file PDF arXiv hợp lệ."""
    assert len(ALL_PDF_FILES) >= 1, "Thư mục raw_data không chứa tệp PDF nào."
    assert any("2503.01333v1.pdf" in p.name for p in ALL_PDF_FILES), (
        "Cần có tệp 2503.01333v1.pdf để làm bài kiểm thử chuẩn."
    )


@pytest.mark.parametrize("pdf_path", ALL_PDF_FILES[:3], ids=lambda p: p.name)
def test_raw_data_parsing_integrity(pdf_path: Path) -> None:
    """Kiểm tra tầng trích xuất văn bản & cắt chunks của từng bài báo arXiv."""
    doc_id = f"test_{pdf_path.stem}"
    parsed = process_pdf(pdf_path, doc_id)

    assert parsed.metadata.page_count > 0, f"File {pdf_path.name} có số trang = 0"
    assert len(parsed.chunks) > 0, f"File {pdf_path.name} không sinh ra chunk nào"
    assert len(parsed.pages) == parsed.metadata.page_count

    # Kiểm tra tính toàn vẹn của chunk đầu tiên
    first_chunk = parsed.chunks[0]
    assert len(first_chunk.text.strip()) > 50, "Chunk đầu tiên quá ngắn hoặc rỗng"
    assert len(first_chunk.page_numbers) >= 1


@pytest.mark.skipif(not settings.gemini_api_key, reason="Cần GEMINI_API_KEY để chạy E2E RAG.")
def test_end_to_end_rag_on_arxiv_paper() -> None:
    """Kiểm thử toàn trình E2E RAG: Parse -> Vectorize -> BM25 -> Rerank -> LLM Answer."""
    paper_path = RAW_DATA_DIR / "2503.01333v1.pdf"
    assert paper_path.is_file(), f"Không tìm thấy {paper_path}"

    document_id = "doc_test_grpo_e2e"
    parsed_doc = process_pdf(paper_path, document_id)

    # Khởi tạo pipeline RAG với Gemini Provider thật
    embedding_provider = GeminiEmbeddingProvider(api_key=settings.gemini_api_key)
    embedding_service = EmbeddingService(embedding_provider)
    vector_store = InMemoryVectorStore()
    bm25_retriever = BM25Retriever()
    reranker = MockReranker()

    hybrid_service = HybridSearchService(
        embedding_service=embedding_service,
        vector_store=vector_store,
        bm25_retriever=bm25_retriever,
        reranker=reranker,
    )

    # 1. Đánh chỉ mục chunks
    indexed_count = hybrid_service.index_chunks(parsed_doc.chunks)
    assert indexed_count == len(parsed_doc.chunks)

    # 2. Kiểm thử Search
    query = "Phương pháp GRPO trong bài báo này giải quyết bài toán gì?"
    search_results = hybrid_service.search(query=query, top_k=3, document_id=document_id)
    assert len(search_results) > 0
    # Top-1 chunk phải liên quan tới GRPO hoặc captioning
    top_snippet = search_results[0].text.lower()
    assert any(term in top_snippet for term in ["grpo", "caption", "policy", "relative", "optimization"])

    # 3. Kiểm thử RAG Answer Generation
    llm_provider = GeminiProvider(api_key=settings.gemini_api_key)
    context_builder = ContextBuilder(max_context_tokens=2000)
    rag_service = RAGService(
        retrieval_service=hybrid_service,
        context_builder=context_builder,
        llm_provider=llm_provider,
    )

    rag_answer = rag_service.answer_question(
        query=query,
        document_id=document_id,
        top_k=3,
    )

    # Kiểm tra chất lượng câu trả lời
    assert rag_answer.answer is not None
    assert len(rag_answer.answer) > 50, "Câu trả lời quá ngắn"
    assert "Thông tin này không được đề cập" not in rag_answer.answer, (
        f"RAG bị từ chối trả lời dù tài liệu có thông tin: {rag_answer.answer}"
    )
    assert len(rag_answer.sources) >= 1, "RAG phải trả về ít nhất 1 nguồn trích dẫn"
    assert rag_answer.sources[0].page_numbers, "Nguồn trích dẫn phải có số trang"

