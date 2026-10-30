"""Script nạp toàn bộ tài liệu từ raw_data/ vào cơ sở dữ liệu và chỉ mục Hybrid Search của DocMind."""

import logging
import sys
from pathlib import Path

# Đảm bảo đường dẫn backend nằm trong sys.path
backend_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_root))

from app.api.deps import _hybrid_search_service
from app.core.logging import setup_logging
from app.db.models import Base
from app.db.seeder import seed_base_data_and_warmup
from app.db.session import SessionLocal, engine


def main() -> None:
    setup_logging()
    logger = logging.getLogger("seed_raw_data")
    logger.info("=== Bắt đầu nạp Base Data từ raw_data ===")

    # Đảm bảo bảng CSDL đã được tạo
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db_session:
        stats = seed_base_data_and_warmup(db=db_session, search_service=_hybrid_search_service)

    logger.info("=== Kết quả nạp Base Data ===")
    logger.info("Tài liệu mới đã nạp: %d", stats["seeded_documents"])
    logger.info("Chunks mới tạo: %d", stats["new_chunks"])
    logger.info("Tổng tài liệu trong CSDL: %d", stats["total_active_documents"])
    logger.info("Tổng chunks trong chỉ mục Hybrid Search: %d", stats["total_indexed_chunks"])
    logger.info("=== Hoàn tất nạp Base Data thành công! ===")


if __name__ == "__main__":
    main()

