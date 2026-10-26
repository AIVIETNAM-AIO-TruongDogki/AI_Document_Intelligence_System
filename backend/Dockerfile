# ==========================================
# STAGE 1: Builder (Compile dependencies)
# ==========================================
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY app ./app
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# ==========================================
# STAGE 2: Runner (Minimal production image)
# ==========================================
FROM python:3.11-slim AS runner

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    mupdf-tools \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed site-packages từ builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy toàn bộ mã nguồn
COPY . .

# Thiết lập user non-root & shared uploads directory
RUN useradd -m -u 1000 appuser && \
    mkdir -p /tmp/uploads && \
    chown -R appuser:appuser /app /tmp/uploads

USER appuser

EXPOSE 8000

# Lệnh mặc định chạy FastAPI Web API (có thể override ở compose để chạy worker)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
