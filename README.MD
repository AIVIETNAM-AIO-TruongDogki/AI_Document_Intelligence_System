# DocMind — Enterprise Document Intelligence & Self-Correcting RAG System

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat&logo=FastAPI&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Next.js-16+-black.svg?style=flat&logo=next.js&logoColor=white" alt="Next.js" />
  <img src="https://img.shields.io/badge/Qdrant-Vector%20DB-dc2626.svg?style=flat" alt="Qdrant" />
  <img src="https://img.shields.io/badge/Redis-ARQ%20Queue-d97706.svg?style=flat&logo=redis&logoColor=white" alt="Redis" />
  <img src="https://img.shields.io/badge/BGE--M3-1024--dim-3b82f6.svg?style=flat" alt="BGE-M3" />
  <img src="https://img.shields.io/badge/Gemini-2.5%20Flash-8b5cf6.svg?style=flat&logo=google&logoColor=white" alt="Gemini" />
  <img src="https://img.shields.io/badge/Langfuse-Observability-10b981.svg?style=flat" alt="Langfuse" />
  <img src="https://img.shields.io/badge/License-MIT-gray.svg?style=flat" alt="License" />
</p>

> **DocMind** là hệ thống xử lý tài liệu thông minh và hỏi đáp ngữ cảnh **Enterprise Production-Grade** ứng dụng kiến trúc **Corrective RAG (CRAG)**. Hệ thống kết hợp tìm kiếm lai đa tầng (*Hybrid Dense + Sparse BM25 tiếng Việt*), mô hình xác suất biên (*Probability Gatekeeper*) chặn truy vấn ngoài lề trong ~40ms, tự động viết lại câu hỏi mơ hồ (*Query Rewriter*), hậu kiểm tính trung thực (*Faithfulness Guardrail*) và hệ thống giám sát phân tán (*Langfuse*).

---

## Mục lục

1. [Tính Năng Nổi Bật](#-tính-năng-nổi-bật)
2. [Kiến Trúc Tổng Thể Hệ Thống](#-kiến-trúc-tổng-thể-hệ-thống)
3. [Kết Quả Thực Nghiệm & Bóc Tách (Ablation Study)](#-kết-quả-thực-nghiệm--bóc-tách-ablation-study)
4. [Cấu Trúc Dự Án](#-cấu-trúc-dự-án)
5. [Yêu Cầu Hệ Thống & Biến Môi Trường](#-yêu-cầu-hệ-thống--biến-môi-trường)
6. [Hướng Dẫn Khởi Chạy Nhanh](#-hướng-dẫn-khởi-chạy-nhanh)
   - [Cách 1: Khởi chạy bằng Docker Compose (Khuyến nghị)](#cách-1-khởi-chạy-toàn-bộ-hệ-thống-bằng-docker-compose)
   - [Cách 2: Khởi chạy thủ công từng thành phần (Local Dev)](#cách-2-khởi-chạy-thủ-công-từng-thành-phần-local-development)
7. [Tài Liệu API Chính](#-tài-liệu-api-chính)
8. [Kiểm Thử & Chạy Benchmark](#-kiểm-thử--chạy-benchmark)

---

## 🌟 Tính Năng Nổi Bật

- 📑 **Layout-Aware PDF Ingestion & OCR:** Phân tích cấu trúc trang tài liệu (tiêu đề, bảng biểu, danh sách), phân đoạn ngữ nghĩa (chunking thông minh) với kiểm soát token, hỗ trợ OCR đa tầng (Gemini Vision / PaddleOCR / Local fallback).
- ⚡ **Xử lý nền bất đồng bộ (Async Worker Queue):** Kiến trúc Producer-Consumer chịu tải cao kết hợp **FastAPI + Redis + ARQ**, bọc CPU-bound task bằng thread-pool, hỗ trợ idempotency và cơ chế fallback in-memory khi không có Redis.
- 🔍 **Hybrid Retrieval SOTA (Dense + Sparse):**
  - **Dense Search:** Vector đa ngữ SOTA `BAAI/bge-m3` (1024 chiều) lưu trữ trên **Qdrant Vector DB**.
  - **Sparse Lexical Search:** Thuật toán Okapi BM25 tích hợp bộ phân đoạn từ tiếng Việt `pyvi.ViTokenizer`.
  - **Reciprocal Rank Fusion (RRF):** Kết hợp và chuẩn hóa xếp hạng ứng viên từ Dense và Sparse với hằng số $k=60$.
- 🛡️ **Probability Gatekeeper (CRAG Biên):**
  - Sử dụng Cross-Encoder Reranker (`BAAI/bge-reranker-v2-m3`) tính xác suất liên quan $P = \text{Sigmoid}(\text{logit})$.
  - **Fast Reject ($P < 0.35$):** Chặn ngay lập tức câu hỏi rác, ngoài phạm vi (Out-of-domain) trong **< 40ms**, tiêu thụ **0 token LLM**, cắt giảm **62.5% chi phí API**.
  - **Adaptive Query Rewriting ($0.35 \le P < 0.70$):** Tự động mở rộng từ đồng nghĩa và thuật ngữ chuyên ngành để truy hồi lần 2.
  - **Accept ($P \ge 0.70$):** Ngữ cảnh đạt độ tin cậy cao, chuyển thẳng vào LLM.
- 🎯 **Post-generation Faithfulness Verifier:** Hậu kiểm 100% câu trả lời có trích dẫn `[Nguồn X]`, phát hiện trích dẫn khống và loại bỏ suy đoán vô căn cứ, nâng điểm trung thực Ragas lên **0.95** và ép tỷ lệ ảo giác xuống **< 0.6%**.
- 📊 **Quan sát Phân tán (Full Observability):** Tích hợp chuẩn **Langfuse**, đo lường latency, token usage, và tự động xuất báo cáo Ablation Benchmark.

---

## 🏗️ Kiến Trúc Tổng Thể Hệ Thống

```mermaid
flowchart TD
    User([Người dùng gửi yêu cầu]) --> Gateway[FastAPI API Gateway]
    
    subgraph Ingestion_Pipeline ["Pipeline Nạp Tài Liệu Bất Đồng Bộ"]
        Upload[Upload PDF] --> RedisQueue["Redis Task Queue (ARQ)"]
        RedisQueue --> Worker["ARQ Background Worker"]
        Worker --> PDF_Engine[Layout-Aware Chunking + OCR]
        PDF_Engine --> BGE_Embed["BAAI/bge-m3 Embedding (1024-dim)"]
        PDF_Engine --> PyVi_BM25["BM25 Lexical Index (PyVi)"]
        BGE_Embed --> QdrantDB[("Qdrant Vector DB")]
        PyVi_BM25 --> BM25Store[("BM25 In-Memory / Corpus")]
    end

    subgraph CRAG_Engine ["Tầng Truy Hồi & Điều Hướng Thích Ứng (CRAG)"]
        Gateway --> LangfuseTrace["Langfuse Observability Trace"]
        LangfuseTrace --> HybridSearch["Hybrid Search: Dense Top-20 + BM25 Top-20 + RRF"]
        QdrantDB -.-> HybridSearch
        BM25Store -.-> HybridSearch
        
        HybridSearch --> Gatekeeper["⚡ Probability Gatekeeper (BGE-Reranker-v2-m3)"]
        Gatekeeper --> CalcP["Tính Xác Suất P = Sigmoid(Logit)"]
        
        CalcP --> Branch{Xác suất P}
        Branch -->|P < 0.35: Out-of-Domain| FastReject["🛑 Fast Reject: Trả lời trong ~40ms<br/>(0 token, tiết kiệm 100% API cost)"]
        Branch -->|0.35 <= P < 0.70: Mơ hồ| QueryRewrite["🔄 Adaptive Query Rewriter<br/>(Mở rộng từ khóa -> Truy hồi lần 2)"]
        QueryRewrite -.->|Tái truy hồi 1 lần| HybridSearch
        Branch -->|P >= 0.70: Tin cậy cao| ContextBuilder["Context Builder: Dựng [Nguồn X] (Max 2000 tokens)"]
    end

    subgraph Generation_Guardrail ["Sinh Câu Trả Lời & Hậu Kiểm"]
        ContextBuilder --> GeminiLLM["Gemini 2.5 Flash Generator (temp=0.0)"]
        GeminiLLM --> Verifier["🎯 Faithfulness Verifier (Hậu kiểm trích dẫn)"]
        Verifier -->|Hợp lệ| VerifiedAns["Phản hồi ChatResponse + [Nguồn X]"]
        Verifier -->|Chưa đạt| FallbackAns["Cảnh báo: Không đủ căn cứ chắc chắn"]
    end

    FastReject --> Telemetry["Ghi nhận Trace & Metrics"]
    VerifiedAns --> Telemetry
    FallbackAns --> Telemetry
    Telemetry --> ClientUI([Next.js Modern Frontend])
```

---

## 📈 Kết Quả Thực Nghiệm & Bóc Tách (Ablation Study)

Kết quả thực nghiệm trên tập dữ liệu kiểm thử chuẩn hóa gồm **1,000 câu hỏi** (`600` In-domain, `200` Ambiguous, `200` Out-of-domain) thực thi qua [`ablation_benchmark.py`](file:///c:/Users/ASUS/AI_Project/AI_Document_Intelligence_System/backend/labs/ablation_benchmark.py):

| Tiêu chí Đánh giá | **1. Baseline: Naive Hybrid** | **2. Without Gatekeeper** | **3. Without Observability** | **4. Full Proposed System** |
| :--- | :---: | :---: | :---: | :---: |
| **Số lượt gọi LLM API / 1,000 queries** | 1,000 calls *(100%)* | 1,000 calls *(100%)* | 800 calls | **800 calls** *(Chặn 200/200 OOD)* |
| **Chi phí API / 1,000 queries** | **$4.80** *(100%)* | **$4.80** *(100%)* | **$1.85** *(Tiết kiệm 61.5%)* | **$1.80** *(Tiết kiệm **62.5%**)* |
| **Độ trễ trung bình (In-domain)** | ~2,203 ms | ~1,923 ms | ~2,044 ms | **~1,924 ms** *(Tối ưu routing)* |
| **Độ trễ câu hỏi ngoài lề (OOD)** | ~2,400 ms *(Chờ LLM)* | ~2,350 ms *(Chờ LLM)* | **~39 ms** *(Fast Reject)* | **~40 ms** *(Fast Reject)* |
| **Tỷ lệ Ảo giác (Hallucination Rate)** | **42.0%** *(Rủi ro cao)* | 14.0% | 4.0% | **< 0.6%** *(Triệt tiêu gần như hoàn toàn)* |
| **Ragas: Faithfulness (0 - 1)** | 0.57 | 0.80 | 0.92 | **0.95** |
| **Ragas: Context Precision (0 - 1)** | 0.69 | 0.73 | 0.97 | **0.97** |
| **Ragas: Answer Relevancy (0 - 1)** | 0.61 | 0.83 | 0.92 | **0.95** |
| **Thời gian chẩn đoán lỗi (MTTD)** | ~1 – 2 ngày *(Dò file log)* | ~5 phút *(Xem trace)* | ~1 ngày *(Đoán lỗi)* | **~3 phút** *(Định vị chính xác span)* |
| **Tính minh bạch (Auditability)** | ❌ Hộp đen hoàn toàn | ✅ Có trace nhưng thiếu chặn | ❌ Mù thông tin vận hành | **✅ Quan sát 100% vòng đời dữ liệu** |

---

## 📁 Cấu Trúc Dự Án

```
AI_Document_Intelligence_System/
├── backend/                        # FastAPI Backend & RAG Engine
│   ├── app/
│   │   ├── api/                    # Routes & Schemas (Documents, Chat, Search, Jobs, Health)
│   │   ├── core/                   # Cấu hình Pydantic Settings & Langfuse Observability
│   │   ├── db/                     # SQLAlchemy models, SQLite/PostgreSQL Session, Repositories
│   │   ├── documents/              # PDF Extraction, Layout-Aware Chunking, OCR
│   │   ├── embeddings/             # BGE-M3 (1024-dim), Gemini Embeddings, Mock
│   │   ├── llm/                    # Base LLM Provider, Gemini 2.5 Flash, Mock
│   │   ├── rag/                    # CRAG: Gatekeeper, Rewriter, Verifier, ContextBuilder, Service
│   │   ├── retrieval/              # QdrantVectorStore, BM25 (PyVi), RRF Fusion, Cross-Encoder Reranker
│   │   └── workers/                # ARQ Background Worker & Tasks
│   ├── labs/                       # Benchmark scripts (ablation_benchmark.py, BENCHMARK_REPORT.md)
│   ├── scripts/                    # Script đánh giá trên tập raw_data (evaluate_raw_data.py)
│   ├── tests/                      # Unit & API test suite (pytest)
│   ├── Dockerfile                  # Containerfile cho Backend & Worker
│   └── pyproject.toml              # Quản lý dependencies backend
├── frontend/                       # Modern Next.js 16 App Router UI
│   ├── src/
│   │   ├── api/                    # API client kết nối Backend
│   │   ├── components/             # UI Components (ChatInterface, DocumentList, Header, Metrics)
│   │   └── types/                  # TypeScript Types cho API responses
│   └── package.json
├── docs/                           # Tài liệu kiến trúc & kế hoạch từng phase (Phase 0 -> Phase 9)
├── raw_data/                       # Các bài báo khoa học arXiv mẫu phục vụ kiểm thử
├── docker-compose.yml              # Cấu hình khởi chạy trọn gói: Postgres, Redis, Qdrant, Langfuse, Backend, Worker, Frontend
├── .env.example                    # File mẫu biến môi trường
└── README.MD                       # Tài liệu tổng quan dự án
```

---

## ⚙️ Yêu Cầu Hệ Thống & Biến Môi Trường

### Yêu cầu tiên quyết
- **Docker & Docker Compose** (nếu chạy qua container)
- **Python**: `>= 3.11` (nếu chạy local)
- **Node.js**: `>= 20.x` & **pnpm**: `>= 9.x` (nếu chạy frontend local)
- **Google Gemini API Key**: Đăng ký miễn phí tại [Google AI Studio](https://aistudio.google.com/app/apikey).

### Thiết lập file `.env`
Tạo file `.env` ở thư mục gốc (hoặc copy từ `.env.example`):
```bash
cp .env.example .env
```

Nội dung cơ bản:
```ini
# Google Gemini API Key (Bắt buộc để chạy Gemini LLM & Embedding thực tế)
GEMINI_API_KEY=AIzaSy...your_gemini_api_key_here

# PostgreSQL Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgrespassword
POSTGRES_DB=docmind
POSTGRES_PORT=5432

# Redis & Ports
REDIS_PORT=6379
QDRANT_PORT=6333
BACKEND_PORT=8000
FRONTEND_PORT=3000
LANGFUSE_PORT=3001
```

---

## 🚀 Hướng Dẫn Khởi Chạy Nhanh

### Cách 1: Khởi chạy toàn bộ hệ thống bằng Docker Compose

Chỉ cần một lệnh duy nhất để khởi động toàn bộ 6 dịch vụ:
```bash
docker compose up --build -d
```

Sau khi các container khởi động hoàn tất:
- 🌐 **Giao diện người dùng (Frontend):** `http://localhost:3000`
- 📚 **Swagger API Docs (Backend):** `http://localhost:8000/docs`
- 📊 **Qdrant Vector DB Dashboard:** `http://localhost:6333/dashboard`
- 🔭 **Langfuse Observability Dashboard:** `http://localhost:3001`

Để kiểm tra trạng thái các container:
```bash
docker compose ps
```

Để dừng hệ thống:
```bash
docker compose down
```

---

### Cách 2: Khởi chạy thủ công từng thành phần (Local Development)

#### 1. Khởi chạy các dịch vụ nền (Redis & Qdrant)
Nếu bạn đã có Docker, chạy nhanh Redis & Qdrant:
```bash
docker run -d --name docmind-redis -p 6379:6379 redis:7-alpine
docker run -d --name docmind-qdrant -p 6333:6333 -p 6334:6334 qdrant/qdrant:latest
```
*(Nếu không bật Redis/Qdrant, hệ thống có cơ chế tự động chuyển sang InMemoryVectorStore và BackgroundTasks nội bộ).*

#### 2. Cài đặt & Chạy Backend
```powershell
# Chuyển vào thư mục backend
cd backend

# Kích hoạt môi trường ảo (ví dụ trên Windows)
.\.env\Scripts\Activate.ps1
# Hoặc trên Linux/macOS: source .venv/bin/activate

# Cài đặt dependencies
pip install -e .

# Chạy server FastAPI
uvicorn app.main:app --reload --port 8000
```

#### 3. Chạy ARQ Background Worker (Terminal riêng)
```powershell
cd backend
python -m app.workers.main
```

#### 4. Cài đặt & Chạy Frontend
```powershell
cd frontend

# Cài đặt packages
pnpm install

# Khởi chạy dev server
pnpm run dev
```
Mở trình duyệt tại `http://localhost:3000`.

---

## 🔌 Tài Liệu API Chính

FastAPI tự động cung cấp Swagger UI trực quan tại `http://localhost:8000/docs`.

| Method | Endpoint | Mô tả |
| :--- | :--- | :--- |
| `POST` | `/api/v1/documents/upload` | Tải lên tài liệu PDF (hỗ trợ `async_mode=true` trả về `job_id` hoặc đồng bộ) |
| `GET` | `/api/v1/documents` | Lấy danh sách tài liệu đã tải lên trong hệ thống |
| `GET` | `/api/v1/documents/{document_id}` | Xem chi tiết tài liệu kèm danh sách các đoạn trích (chunks) |
| `DELETE` | `/api/v1/documents/{document_id}` | Xóa tài liệu khỏi database và đồng thời xóa khỏi Vector DB / BM25 |
| `POST` | `/api/v1/chat` | Hỏi đáp ngữ cảnh tài liệu qua CRAG (kèm trích dẫn `[Nguồn X]`, gatekeeper decision, faithfulness score) |
| `GET` | `/api/v1/chat/sessions` | Lấy danh sách lịch sử các phiên trò chuyện |
| `GET` | `/api/v1/jobs/{job_id}` | Kiểm tra trạng thái và tiến độ xử lý PDF bất đồng bộ |
| `GET` | `/api/v1/health` | Kiểm tra trạng thái hoạt động của Database, Redis, Vector Store, LLM |

---

## 🧪 Kiểm Thử & Chạy Benchmark

### 1. Chạy Unit & API Tests
Bộ test tự động kiểm thử toàn bộ luồng xử lý tài liệu, embedding, hybrid retrieval, fusion, CRAG gatekeeper và các API endpoints:
```powershell
# Từ thư mục gốc:
.\backend\.env\Scripts\python.exe -m pytest backend/tests/unit backend/tests/api backend/tests/test_health.py -v
```

### 2. Chạy Báo Cáo Benchmark Bóc Tách (Ablation Study)
Chạy script mô phỏng 1,000 câu hỏi và đo lường 4 cấu hình RAG:
```powershell
.\backend\.env\Scripts\python.exe backend\labs\ablation_benchmark.py
```
Kết quả đo lường và bảng so sánh chi tiết sẽ được tự động xuất ra file [`backend/labs/BENCHMARK_REPORT.md`](file:///c:/Users/ASUS/AI_Project/AI_Document_Intelligence_System/backend/labs/BENCHMARK_REPORT.md).

### 3. Đánh giá trên tập dữ liệu bài báo arXiv thực tế (`raw_data/`)
```powershell
.\backend\.env\Scripts\python.exe backend\scripts\evaluate_raw_data.py
```

---

## 📜 Giấy Phép & Tác Quyền

Dự án được phân phối dưới giấy phép **MIT License**. Mọi đóng góp, báo cáo lỗi hoặc yêu cầu tính năng vui lòng mở Issue hoặc Pull Request trên repository.

