from app.documents.models import ParsedDocument
from app.embeddings.mock import MockEmbeddingProvider
from app.embeddings.service import EmbeddingService
from app.retrieval.service import SearchService
from app.retrieval.vector_store import BaseVectorStore, InMemoryVectorStore

# Khởi tạo các singleton service cho tầng API
# (Sau này khi có Qdrant/PostgreSQL, chỉ cần thay đổi tại file này)
_vector_store: BaseVectorStore = InMemoryVectorStore()
_embedding_provider = MockEmbeddingProvider(dimension=64)
_embedding_service = EmbeddingService(_embedding_provider)
_search_service = SearchService(_embedding_service, _vector_store)

# Lưu trữ cache các tài liệu đã upload trong bộ nhớ
_documents_store: dict[str, ParsedDocument] = {}


def get_vector_store() -> BaseVectorStore:
    """Dependency cung cấp Vector Store."""
    return _vector_store


def get_embedding_service() -> EmbeddingService:
    """Dependency cung cấp Embedding Service."""
    return _embedding_service


def get_search_service() -> SearchService:
    """Dependency cung cấp Search Service."""
    return _search_service


def get_documents_store() -> dict[str, ParsedDocument]:
    """Dependency cung cấp kho lưu trữ tài liệu."""
    return _documents_store
