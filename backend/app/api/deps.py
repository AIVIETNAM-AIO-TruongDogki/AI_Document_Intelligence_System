from app.documents.models import ParsedDocument
from app.embeddings.mock import MockEmbeddingProvider
from app.embeddings.service import EmbeddingService
from app.llm.base import MockLLMProvider
from app.rag.context_builder import ContextBuilder
from app.rag.service import RAGService
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.reranker import MockReranker
from app.retrieval.service import HybridSearchService, SearchService
from app.retrieval.vector_store import BaseVectorStore, InMemoryVectorStore

# Khởi tạo các singleton service cho tầng API
# (Sau này khi có Qdrant/PostgreSQL, chỉ cần thay đổi tại file này)
_vector_store: BaseVectorStore = InMemoryVectorStore()
_embedding_provider = MockEmbeddingProvider(dimension=64)
_embedding_service = EmbeddingService(_embedding_provider)
_search_service = SearchService(_embedding_service, _vector_store)

# Khởi tạo RAG Pipeline Singletons
_bm25_retriever = BM25Retriever()
_reranker = MockReranker()
_hybrid_search_service = HybridSearchService(
    embedding_service=_embedding_service,
    vector_store=_vector_store,
    bm25_retriever=_bm25_retriever,
    reranker=_reranker,
)
from app.core.config import settings
from app.llm.base import BaseLLMProvider
from app.llm.gemini import GeminiProvider

_context_builder = ContextBuilder(max_context_tokens=2000)
_llm_provider: BaseLLMProvider
if settings.gemini_api_key:
    _llm_provider = GeminiProvider(api_key=settings.gemini_api_key)
else:
    _llm_provider = MockLLMProvider()

_rag_service = RAGService(
    retrieval_service=_hybrid_search_service,
    context_builder=_context_builder,
    llm_provider=_llm_provider,
)

# Cung cấp dependency cho document repository
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.repositories.chat_repo import ChatRepository
from app.db.repositories.document_repo import DocumentRepository
from app.db.session import get_db

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


def get_rag_service() -> RAGService:
    """Dependency cung cấp RAG Service."""
    return _rag_service


def get_document_repo(db: Annotated[Session, Depends(get_db)]) -> DocumentRepository:
    return DocumentRepository(db)


def get_chat_repo(db: Annotated[Session, Depends(get_db)]) -> ChatRepository:
    return ChatRepository(db)