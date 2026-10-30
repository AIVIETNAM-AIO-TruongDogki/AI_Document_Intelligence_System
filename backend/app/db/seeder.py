import logging
from dataclasses import replace
from pathlib import Path

from sqlalchemy.orm import Session

from app.db.models import ChunkModel, DocumentModel
from app.db.repositories.document_repo import DocumentRepository
from app.documents.models import Chunk
from app.documents.service import process_pdf
from app.retrieval.service import HybridSearchService

logger = logging.getLogger(__name__)


def locate_raw_data_dir() -> Path | None:
    """Xác định vị trí thư mục raw_data linh hoạt theo môi trường làm việc."""
    candidates = [
        Path("raw_data"),
        Path('../raw_data'),
        Path('/app/raw_data'),
        Path(__file__).resolve().parent.parent.parent / "raw_data",
        Path(__file__).resolve().parent.parent.parent.parent / "raw_data",
    ]
    for p in candidates:
        if p.is_dir():
            return p.resolve()
    return None


def seed_base_data_and_warmup(
    db: Session,
    search_service: HybridSearchService,
    raw_dir: Path | None = None,
) -> dict[str, int]:
    """Tự động nạp toàn bộ PDF trong raw_data vào CSDL và đồng bộ BM25 & Vector Store.

    1. Quét các file .pdf trong raw_data.
    2. Nếu file chưa có trong CSDL (DocumentModel), phân tích và lưu vào CSDL.
    3. Nạp toàn bộ chunks trong CSDL vào BM25Retriever và VectorStore nếu bộ nhớ chưa được nạp.
    """
    target_dir = raw_dir or locate_raw_data_dir()
    doc_repo = DocumentRepository(db)
    existing_docs = {d.filename: d for d in doc_repo.list_documents()}

    new_seeded_count = 0
    new_chunks_count = 0

    if target_dir and target_dir.exists():
        pdf_files = sorted(target_dir.glob("*.pdf"))
        logger.info("Tìm thấy %d file PDF trong thư mục %s", len(pdf_files), target_dir)

        for pdf_path in pdf_files:
            filename = pdf_path.name
            if filename in existing_docs:
                logger.info("Tài liệu cơ sở '%s' đã tồn tại trong CSDL, bỏ qua phân tích lại.", filename)
                continue

            clean_stem = pdf_path.stem.replace(".", "_").replace("-", "_").replace(" ", "_")
            doc_id = f"base_doc_{clean_stem}"

            try:
                logger.info("Đang xử lý tài liệu cơ sở: %s ...", filename)
                parsed_doc = process_pdf(path=pdf_path, document_id=doc_id)
                parsed_doc = replace(
                    parsed_doc,
                    metadata=replace(parsed_doc.metadata, filename=filename),
                )

                file_size = pdf_path.stat().st_size
                doc_repo.save_parsed_document(parsed_doc, file_size=file_size)
                search_service.index_chunks(parsed_doc.chunks)

                existing_docs[filename] = doc_repo.get_by_id(doc_id)  # type: ignore[assignment]
                new_seeded_count += 1
                new_chunks_count += len(parsed_doc.chunks)
                logger.info(
                    "Đã nạp thành công '%s': %d trang, %d chunks.",
                    filename,
                    parsed_doc.metadata.page_count,
                    len(parsed_doc.chunks),
                )
            except Exception as exc:
                logger.error("Lỗi khi nạp tài liệu cơ sở '%s': %s", filename, exc, exc_info=True)
                db.rollback()

    # 4. Kiểm tra Warmup cho Hybrid Search: Đảm bảo BM25 và VectorStore luôn đầy đủ
    current_indexed_chunks = len(getattr(search_service.bm25_retriever, "_corpus", {}))
    total_db_chunks = db.query(ChunkModel).count()

    if current_indexed_chunks < total_db_chunks:
        logger.info(
            "Đang làm nóng Hybrid Search: Chỉ mục hiện có %d chunks, CSDL có %d chunks. Đang đồng bộ...",
            current_indexed_chunks,
            total_db_chunks,
        )
        all_chunk_records = db.query(ChunkModel).all()
        chunks_to_index = [
            Chunk(
                chunk_id=c.id,
                document_id=c.document_id,
                text=c.text,
                token_count=c.token_count,
                page_numbers=tuple(c.page_numbers or []),
            )
            for c in all_chunk_records
        ]
        search_service.index_chunks(chunks_to_index)
        logger.info("Đã làm nóng thành công %d chunks vào BM25 và Vector Store.", len(chunks_to_index))

    return {
        "seeded_documents": new_seeded_count,
        "new_chunks": new_chunks_count,
        "total_active_documents": len(doc_repo.list_documents()),
        "total_indexed_chunks": len(getattr(search_service.bm25_retriever, "_corpus", {})),
    }


