import argparse
import sys
import time
from pathlib import Path

# Đảm bảo UTF-8 cho console Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Thêm đường dẫn backend vào sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
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

# Danh mục bài test chuẩn mực cho từng bài báo arXiv trong raw_data
BENCHMARK_CASES = {
    "2405.17247v1.pdf": {
        "title": "An Introduction to Vision-Language Modeling",
        "queries": [
            "Vision Language Model là gì và các thành phần cốt lõi của nó là gì?",
            "What are the main training objectives for vision-language models discussed in the paper?",
        ],
    },
    "2503.01333v1.pdf": {
        "title": "Group Relative Policy Optimization for Image Captioning",
        "queries": [
            "Phương pháp GRPO trong bài báo này giải quyết bài toán gì và có ưu điểm gì so với PPO?",
        ],
    },
    "189_Q_Insight_Understanding_Im.pdf": {
        "title": "Q-Insight: Understanding Image Quality via Visual Reinforcement Learning",
        "queries": [
            "Mô hình Q-Insight đánh giá chất lượng hình ảnh (Image Quality Assessment) như thế nào?",
        ],
    },
    "2505.19877v1.pdf": {
        "title": "Vad-R1: Towards Video Anomaly Reasoning",
        "queries": [
            "Mô hình Vad-R1 tiếp cận bài toán Video Anomaly Reasoning qua chuỗi tư duy (Chain-of-Thought) như thế nào?",
        ],
    },
    "2511.10055v1.pdf": {
        "title": "Image Aesthetic Reasoning via HCM-GRPO",
        "queries": [
            "Phương pháp HCM-GRPO được áp dụng vào bài toán đánh giá thẩm mỹ hình ảnh (Image Aesthetic) như thế nào?",
        ],
    },
    "2606.29915v1.pdf": {
        "title": "H-GRPO: Permutation-Invariant Reinforcement Learning",
        "queries": [
            "H-GRPO giải quyết thách thức gì trong bài toán suy luận thị giác (Grounded Visual Reasoning)?",
        ],
    },
}


def find_raw_data_dir() -> Path:
    candidates = [
        Path("raw_data"),
        Path("../raw_data"),
        backend_dir.parent / "raw_data",
    ]
    for c in candidates:
        if c.is_dir():
            return c
    raise FileNotFoundError("Không tìm thấy thư mục raw_data chứa PDF.")


def run_evaluation(target_paper: str | None = None, max_chunks: int = 150) -> None:
    raw_dir = find_raw_data_dir()
    pdf_files = list(raw_dir.glob("*.pdf"))

    if not pdf_files:
        print(f"❌ Không tìm thấy file PDF nào trong: {raw_dir}")
        return

    print("=" * 80)
    print("🚀 BẮT ĐẦU CHƯƠNG TRÌNH ĐÁNH GIÁ RAG PIPELINE TRÊN RAW_DATA (ARXIV)")
    print(f"📂 Thư mục dữ liệu: {raw_dir}")
    print(f"🔑 Gemini Model: {settings.ocr_provider} | API Key: {'Đã cấu hình' if settings.gemini_api_key else 'Thiếu'}")
    print("=" * 80)

    # Khởi tạo RAG Pipeline
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

    llm_provider = GeminiProvider(api_key=settings.gemini_api_key)
    context_builder = ContextBuilder(max_context_tokens=2500)
    rag_service = RAGService(
        retrieval_service=hybrid_service,
        context_builder=context_builder,
        llm_provider=llm_provider,
    )

    report_lines: list[str] = [
        "# BÁO CÁO ĐÁNH GIÁ CHẤT LƯỢNG RAG TRÊN TẬP RAW_DATA (ARXIV)",
        f"**Thời gian chạy:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n",
        "| Bài báo | Số trang | Số chunks | Câu hỏi | Nguồn (Trang) | Thời gian (s) | Đánh giá |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    for pdf_path in pdf_files:
        if target_paper and target_paper.lower() not in pdf_path.name.lower():
            continue

        benchmark = BENCHMARK_CASES.get(pdf_path.name, {
            "title": pdf_path.stem,
            "queries": ["Tóm tắt mục tiêu và phương pháp chính của bài báo này?"],
        })

        print(f"\n📄 Đang xử lý: {pdf_path.name} ({benchmark['title']})...")
        t0 = time.time()
        doc_id = f"doc_{pdf_path.stem}"
        parsed_doc = process_pdf(pdf_path, doc_id)
        parse_time = time.time() - t0

        chunks_to_index = parsed_doc.chunks[:max_chunks]
        print(f"   Trích xuất: {parsed_doc.metadata.page_count} trang, {len(parsed_doc.chunks)} chunks (lấy {len(chunks_to_index)} để index) trong {parse_time:.2f}s")

        t_idx = time.time()
        hybrid_service.index_chunks(chunks_to_index)
        print(f"   Vectorize & BM25 Index hoàn tất trong {time.time() - t_idx:.2f}s")

        for query in benchmark["queries"]:
            print(f"\n   ❓ Hỏi: '{query}'")
            t_qa = time.time()
            rag_answer = rag_service.answer_question(query=query, document_id=doc_id, top_k=3)
            qa_time = time.time() - t_qa

            answer_text = rag_answer.answer.strip()
            source_pages = [str(s.page_numbers) for s in rag_answer.sources]
            pages_str = ", ".join(source_pages) if source_pages else "Không có"

            is_abstain = "Thông tin này không được đề cập" in answer_text
            passed = not is_abstain and len(answer_text) > 50

            status_icon = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {status_icon} (Thời gian: {qa_time:.2f}s) | Nguồn: {pages_str}")
            print(f"   💬 Trả lời: {answer_text[:200]}...")

            report_lines.append(
                f"| `{pdf_path.name}` | {parsed_doc.metadata.page_count} | {len(parsed_doc.chunks)} | {query} | {pages_str} | {qa_time:.2f}s | {status_icon} |"
            )

    report_path = backend_dir / "evaluation_report.md"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"\n🎉 Đã hoàn thành đánh giá! Báo cáo chi tiết đã lưu tại: {report_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Đánh giá RAG trên tài liệu raw_data")
    parser.add_argument("--paper", type=str, default=None, help="Chỉ chạy trên 1 bài báo cụ thể")
    parser.add_argument("--max-chunks", type=int, default=100, help="Số chunks tối đa index mỗi bài")
    args = parser.parse_args()
    run_evaluation(target_paper=args.paper, max_chunks=args.max_chunks)

