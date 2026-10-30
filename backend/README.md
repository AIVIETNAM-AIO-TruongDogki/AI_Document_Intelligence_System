# DocMind Backend Service — Enterprise Corrective RAG (CRAG) Engine

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%20|%203.12%20|%203.14-blue.svg" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-0.115+-009688.svg" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Qdrant-Vector%20Store-dc2626.svg" alt="Qdrant" />
  <img src="https://img.shields.io/badge/ARQ-Async%20Task%20Queue-d97706.svg" alt="ARQ" />
  <img src="https://img.shields.io/badge/PyMuPDF-PDF%20Engine-brightgreen.svg" alt="PyMuPDF" />
  <img src="https://img.shields.io/badge/Langfuse-Telemetry-10b981.svg" alt="Langfuse" />
</p>

Backend của **DocMind** là dịch vụ xử lý tài liệu thông minh và lõi hỏi đáp ngữ cảnh **Enterprise Corrective RAG (CRAG)** xây dựng trên nền tảng **FastAPI**, **SQLAlchemy**, **ARQ/Redis** và **Qdrant Vector Database**.

---

## 📑 Mục Lục

1. [Kiến Trúc Tầng Ứng Dụng (Layered Architecture)](#1-kiến-trúc-tầng-ứng-dụng-layered-architecture)
2. [Chi Tiết Các Module Cốt Lõi](#2-chi-tiết-các-module-cốt-lõi)
3. [Cài Đặt & Khởi Chạy Local](#3-cài-đặt--khởi-chạy-local)
4. [Cấu Hình Biến Môi Trường (`.env`)](#4-cấu-hình-biến-môi-trường-env)
5. [Quy Trình Kiểm Thử (Testing Suite)](#5-quy-trình-kiểm-thử-testing-suite)
6. [Thực Nghiệm & Báo Cáo Benchmark (Phase 9)](#6-thực-nghiệm--báo-cáo-benchmark-phase-9)

---

## 1. Kiến Trúc Tầng Ứng Dụng (Layered Architecture)

Mã nguồn backend tuân thủ nguyên lý thiết kế **Dependency Inversion** và **Clean Architecture**:

```
backend/
├── app/
│   ├── api/                    # Tầng giao diện RESTful API
│   │   ├── deps.py             # Dependency Injection Container (Singletons & Repositories)
│   │   ├── routes/             # Endpoints: chat, documents, jobs, health
│   │   └── schemas/            # Pydantic v2 DTOs (Request / Response validation)
│   ├── core/                   # Cấu hình hệ thống & Quan sát
│   │   ├── config.py           # Pydantic Settings đọc biến môi trường
│   │   └── observability.py    # Langfuse telemetry & @observe() decorator
│   ├── db/                     # Tầng lưu trữ cơ sở dữ liệu quan hệ
│   │   ├── models.py           # SQLAlchemy ORM models (Document, Page, Chunk, Job, ChatSession, Message)
│   │   ├── session.py          # Session factory (SQLite / PostgreSQL)
│   │   └── repositories/       # Data Access Layer (DocumentRepo, JobRepo, ChatRepo)
│   ├── documents/              # Pipeline xử lý tài liệu
│   │   ├── parser.py           # PyMuPDF Document Extraction (Layout-Aware)
│   │   ├── chunker.py          # Sliding Window Chunker với ngưỡng token tiktoken
│   │   ├── cleaner.py          # Khử nhiễu văn bản, chuẩn hóa khoảng trắng & ký tự điều khiển
│   │   └── ocr/                # OCR Engine (Gemini OCR, PaddleOCR, Composite fallback)
│   ├── embeddings/             # Tầng biểu diễn Vector
│   │   ├── base.py             # Abstract Base Class cho Embedding Provider
│   │   ├── bge.py              # BGE-M3 Multilingual Embedding (1024 chiều, chuẩn L2)
│   │   ├── gemini.py           # Google Gemini Embedding Provider (Rate-limit retry)
│   │   └── mock.py             # Mock Provider cho kiểm thử offline
│   ├── llm/                    # Tầng sinh văn bản (LLM Providers)
│   │   ├── base.py             # BaseLLMProvider interface
│   │   ├── gemini.py           # Gemini 2.5 Flash Provider (@observe telemetry)
│   │   └── mock.py             # Deterministic Mock Provider
│   ├── rag/                    # Corrective RAG (CRAG) Orchestration
│   │   ├── gatekeeper.py       # Probability Gatekeeper (Fast Reject, Rewrite, Accept)
│   │   ├── rewriter.py         # Adaptive Query Rewriter (Mở rộng từ khóa chuyên ngành)
│   │   ├── verifier.py         # Faithfulness Verifier (Hậu kiểm chống ảo giác [Nguồn X])
│   │   ├── context_builder.py  # Xây dựng khối context có giới hạn ngân sách token
│   │   ├── prompt.py           # System instructions & prompt templates chống ảo giác
│   │   └── service.py          # RAGService điều phối toàn bộ luồng CRAG
│   ├── retrieval/              # Tầng truy hồi dữ liệu
│   │   ├── qdrant_store.py     # Qdrant Vector Store (UUID5 ID, payload filtering, fallback)
│   │   ├── vector_store.py     # BaseVectorStore & InMemoryVectorStore
│   │   ├── bm25.py             # Okapi BM25 Sparse Search (PyVi ViTokenizer cho tiếng Việt)
│   │   ├── fusion.py           # Reciprocal Rank Fusion (RRF k=60)
│   │   ├── reranker.py         # Cross-Encoder Reranker chuẩn hóa Sigmoid: P = 1 / (1 + e^-logit)
│   │   └── service.py          # HybridSearchService (Dense + Sparse + RRF + Rerank)
│   └── workers/                # ARQ Asynchronous Task Queue
│       ├── main.py             # Entrypoint chạy ARQ Consumer
│       ├── tasks.py            # Async ingestion worker bọc CPU-bound qua asyncio.to_thread
│       └── setting.py          # Quản lý Redis Connection Pool & ARQ Settings
├── labs/                       # Nghiên cứu bóc tách & Đo lường
│   ├── ablation_benchmark.py   # Script benchmark 1,000 queries qua 4 cấu hình RAG
│   ├── benchmark_dataset.json  # Dataset phân tầng: 60% In-domain, 20% Ambiguous, 20% OOD
│   └── BENCHMARK_REPORT.md     # Báo cáo kết quả số liệu thực nghiệm
├── scripts/                    # Scripts kiểm thử trên tài liệu raw_data (arXiv)
└── tests/                      # Unit & API test suite
```

---

## 2. Chi Tiết Các Module Cốt Lõi

### 2.1. Ingestion & Task Queue Bất Đồng Bộ
- **API Producer (`/documents/upload`):** Nhận file PDF, lưu tạm vào disk, tạo job trong DB và đẩy task vào Redis queue qua ARQ. Trả về ngay `job_id` (HTTP 202) trong vòng < 20ms.
- **Worker Consumer (`workers/tasks.py`):** Lắng nghe task từ Redis, thực thi:
  1. Parse cấu trúc trang PDF qua PyMuPDF (`fitz`).
  2. Làm sạch văn bản (`TextCleaner`) và cắt chunks kiểm soát token (`DocumentChunker`).
  3. Đánh chỉ mục **đồng thời** vào **Qdrant Vector DB** (`QdrantVectorStore`) và **BM25 Corpus** (`BM25Retriever`).
  4. Lưu cấu trúc phân cấp vào cơ sở dữ liệu và giải phóng file tạm.
- **Worker Concurrency & Heartbeat:** Tác vụ CPU-bound nặng được bọc qua `asyncio.to_thread` nhằm tránh làm nghẽn Asyncio Event Loop, đảm bảo tín hiệu Heartbeat tới Redis không bị gián đoạn.

### 2.2. Corrective RAG (CRAG) & Probability Gatekeeper
- **Cross-Encoder Reranking:** Đầu ra của mô hình được chuẩn hóa bằng hàm Sigmoid để thu được xác suất $P(\text{relevance}) \in [0.0, 1.0]$.
- **Phân luồng thích ứng (Adaptive Routing):**
  - **Fast Reject ($P < 0.35$):** Câu hỏi ngoài phạm vi tri thức tài liệu (Out-of-domain) bị chặn ngay tại biên chỉ trong **~40ms**, tiêu tốn **0 token LLM** và không phát sinh chi phí gọi Gemini.
  - **Adaptive Query Rewrite ($0.35 \le P < 0.70$):** Truy vấn mang tính mơ hồ, gián tiếp được module `QueryRewriter` tự động mở rộng thực thể và từ khóa đồng nghĩa trước khi tái truy hồi lần 2.
  - **Accept ($P \ge 0.70$):** Ngữ cảnh có độ liên quan cao được đóng gói thành định dạng `[Nguồn X]` qua `ContextBuilder` (ngân sách 2000 tokens).

### 2.3. Hậu Kiểm Trung Thực (Faithfulness Verifier)
- Phân tích câu trả lời được sinh ra từ Gemini 2.5 Flash:
  1. Kiểm tra tính hợp lệ của mọi trích dẫn `[Nguồn X]`.
  2. Đối chiếu độ phủ thực thể (Lexical & Entity Grounding) của từng mệnh đề khẳng định với các đoạn bằng chứng.
  3. Tự động loại bỏ các câu suy đoán không có căn cứ hoặc gắn nhãn cảnh báo an toàn nếu điểm trung thực thấp.

---

## 3. Cài Đặt & Khởi Chạy Local

### 3.1. Chuẩn bị môi trường Python
Yêu cầu Python `>= 3.11` (khuyến nghị Python 3.11 hoặc 3.12).

```powershell
# Chuyển vào thư mục backend
cd backend

# Khởi tạo môi trường ảo (Virtual Environment)
python -m venv .env

# Kích hoạt môi trường ảo:
# Trên Windows PowerShell:
.\.env\Scripts\Activate.ps1
# Trên Linux/macOS:
source .env/bin/activate

# Nâng cấp pip và cài đặt package dạng editable
pip install --upgrade pip
pip install -e .
```

### 3.2. Cấu hình biến môi trường
Tạo file `.env.local` hoặc `.env` trong thư mục `backend/`:
```ini
APP_NAME=DocMind
APP_ENV=development
LOG_LEVEL=INFO

# Khóa API Google Gemini (Bắt buộc cho LLM & Gemini Embeddings thực tế)
GEMINI_API_KEY=AIzaSy...your_gemini_key

# Cơ sở dữ liệu (Mặc định SQLite, hoặc PostgreSQL)
DATABASE_URL=sqlite:///./docmind.db

# Redis & Qdrant
REDIS_URL=redis://localhost:6379/0
QDRANT_HOST=localhost
QDRANT_PORT=6333
USE_QDRANT=true

# CRAG & Gatekeeper Thresholds
EMBEDDING_PROVIDER=bge
ENABLE_GATEKEEPERS=true
GATEKEEPER_ACCEPT_THRESHOLD=0.70
GATEKEEPER_REJECT_THRESHOLD=0.35
ENABLE_FAITHFULNESS_VERIFIER=true
```

### 3.3. Khởi động FastAPI API Gateway
```powershell
uvicorn app.main:app --reload --port 8000
```
- Swagger UI có sẵn tại: `http://localhost:8000/docs`
- ReDoc UI có sẵn tại: `http://localhost:8000/redoc`

### 3.4. Khởi động ARQ Background Worker (Terminal riêng)
```powershell
python -m app.workers.main
```

---

## 4. Cấu Hình Biến Môi Trường (`.env`)

| Biến Môi Trường | Mặc Định | Mô Tả |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | `None` | Khóa API Gemini từ Google AI Studio |
| `DATABASE_URL` | `sqlite:///./docmind.db` | Chuỗi kết nối CSDL (SQLite hoặc PostgreSQL) |
| `REDIS_URL` | `redis://localhost:6379/0` | Địa chỉ kết nối Redis Message Broker |
| `QDRANT_HOST` | `localhost` | Hostname của Qdrant Vector DB |
| `QDRANT_PORT` | `6333` | Port HTTP của Qdrant |
| `USE_QDRANT` | `true` | `true`: Dùng Qdrant; `false`: Dùng InMemoryVectorStore |
| `EMBEDDING_PROVIDER` | `bge` | `bge` (BAAI/bge-m3 1024-dim), `gemini`, hoặc `mock` |
| `ENABLE_GATEKEEPER` | `true` | Bật/tắt Probability Gatekeeper (Fast Reject + CRAG Routing) |
| `GATEKEEPER_ACCEPT_THRESHOLD`| `0.70` | Ngưỡng xác suất $P$ chấp nhận trực tiếp |
| `GATEKEEPER_REJECT_THRESHOLD`| `0.35` | Ngưỡng xác suất $P$ từ chối ngay lập tức |
| `ENABLE_FAITHFULNESS_VERIFIER`| `true` | Bật/tắt bộ hậu kiểm tính trung thực câu trả lời |
| `LANGFUSE_PUBLIC_KEY` | `None` | Public key kết nối Langfuse Server |
| `LANGFUSE_SECRET_KEY` | `None` | Secret key kết nối Langfuse Server |
| `LANGFUSE_HOST` | `http://localhost:3001` | URL của Langfuse Server |

---

## 5. Quy Trình Kiểm Thử (Testing Suite)

Hệ thống được kiểm thử toàn diện bằng `pytest`:

```powershell
# Chạy toàn bộ Unit Tests và API Tests
pytest tests/unit tests/api tests/test_health.py -v

# Chạy riêng bộ kiểm thử Corrective RAG (Phase 9)
pytest tests/unit/rag/test_phase9_crag.py -v

# Chạy kiểm thử các tầng Retrieval & Hybrid Search
pytest tests/unit/retrieval -v
```

---

## 6. Thực Nghiệm & Báo Cáo Benchmark (Phase 9)

### 6.1. Chạy Ablation Study (1,000 câu hỏi)
Script [`backend/labs/ablation_benchmark.py`](file:///c:/Users/ASUS/AI_Project/AI_Document_Intelligence_System/backend/labs/ablation_benchmark.py) tự động sinh tập dữ liệu 1,000 câu hỏi phân tầng và đo lường 4 cấu hình RAG:
```powershell
python labs/ablation_benchmark.py
```

### 6.2. Kết quả đo lường chính thức
Báo cáo chi tiết được lưu tại [`backend/labs/BENCHMARK_REPORT.md`](file:///c:/Users/ASUS/AI_Project/AI_Document_Intelligence_System/backend/labs/BENCHMARK_REPORT.md):
- **Cắt giảm chi phí:** Tiết kiệm **62.5%** ngân sách API (từ $4.80 xuống $1.80 / 1,000 queries) nhờ cơ chế Fast Reject chặn 100% câu hỏi Out-of-Domain.
- **Tối ưu độ trễ:** Độ trễ từ chối câu hỏi rác chỉ còn **~40ms** (so với 2,400ms khi phải chờ LLM).
- **Triệt tiêu ảo giác:** Giảm tỷ lệ bịa đặt từ **42.0% xuống < 0.6%**.
- **Độ trung thực (Ragas Faithfulness):** Đạt **0.95/1.0**; **Context Precision** đạt **0.97/1.0**.

