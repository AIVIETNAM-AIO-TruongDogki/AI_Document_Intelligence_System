from sqlalchemy.orm import Session
from app.db.models import DocumentModel, DocumentPageModel, ChunkModel
from app.documents.models import ParsedDocument

class DocumentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def save_parsed_document(self, parsed_doc: ParsedDocument, file_size: int = 0) -> DocumentModel:
        """Lưu toàn bộ ParsedDocument (Document, Pages, Chunks) trong 1 Transaction nguyên tử."""
        doc_model = DocumentModel(
            id=parsed_doc.metadata.document_id,
            filename=parsed_doc.metadata.filename,
            file_size=file_size,
            page_count=parsed_doc.metadata.page_count,
        )
        self.db.add(doc_model)

        for page in parsed_doc.pages:
            page_model = DocumentPageModel(
                document_id=doc_model.id,
                page_number=page.page_number,
                text=page.text,
            )
            self.db.add(page_model)

        for idx, chunk in enumerate(parsed_doc.chunks, start=1):
            chunk_model = ChunkModel(
                id=chunk.chunk_id,
                document_id=doc_model.id,
                text=chunk.text,
                token_count=chunk.token_count,
                page_numbers=list(chunk.page_numbers),
                sequence_number=idx,
            )
            self.db.add(chunk_model)

        self.db.commit()
        self.db.refresh(doc_model)
        return doc_model

    def get_by_id(self, document_id: str) -> DocumentModel | None:
        return self.db.query(DocumentModel).filter(DocumentModel.id == document_id).first()

    def list_documents(self) -> list[DocumentModel]:
        return self.db.query(DocumentModel).order_by(DocumentModel.created_at.desc()).all()
    
    def delete_by_id(self, document_id: str) -> bool:
        try:
            doc = self.get_by_id(document_id)
            if not doc:
                return False
            self.db.delete(doc)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise e
