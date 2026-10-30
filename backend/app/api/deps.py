from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.repositories.chat_repo import ChatRepository
from app.db.repositories.document_repo import DocumentRepository
from app.db.repositories.job_repo import JobRepository
from app.db.session import get_db
from app.documents.models import ParsedDocument
from app.embeddings.base import EmbeddingProvider
from app.embeddings.bge import BGEM3EmbeddingProvider
from app.embeddings.gemini import GeminiEmbeddingProvider
from app.embeddings.mock import MockEmbeddingProvider
from app.embeddings.service import EmbeddingService
from app.llm.base import BaseLLMProvider, MockLLMProvider
from app.llm.gemini import GeminiProvider
from app.rag.context_builder import ContextBuilder
from app.rag.gatekeeper import RAGGatekeeper
from app.rag.rewriter import QueryRewriter
from app.rag.service import RAGService
from app.rag.verifier import FaithfulnessVerifier
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.qdrant_store import QdrantVectorStore
from app.retrieval.reranker import CrossEncoderReranker
from app.retrieval.service import HybridSearchService
from app.retrieval.vector_store import BaseVectorStore, InMemoryVectorStore

# 1. Khởi tạo Embedding Provider (Ưu tiên BGE-M3 1024-dim hoặc Gemini theo cấu hình)
_embedding_provider: EmbeddingProvider
if settings.embedding_provider == "bge":
    _embedding_provider = BGEM3EmbeddingProvider(dimension=1024)
elif settings.gemini_api_key and settings.embedding_provider == "gemini":
    _embedding_provider = GeminiEmbeddingProvider(api_key=settings.gemini_api_key)
else:
    _embedding_provider = MockEmbeddingProvider(dimension=64)

_embedding_service = EmbeddingService(_embedding_provider)

# 2. Khởi tạo Vector Store (QdrantVectorStore kèm InMemory fallback)
_vector_store: BaseVectorStore
if settings.use_qdrant:
    _vector_store = QdrantVectorStore(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
        collection_name=settings.qdrant_collection,
        vector_size=_embedding_provider.dimension,
    )
else:
    _vector_store = InMemoryVectorStore()

# 3. Khởi tạo RAG Pipeline Singletons (BM25 + Dense + CrossEncoder Rerank)
_bm25_retriever = BM25Retriever()
_reranker = CrossEncoderReranker()
_hybrid_search_service = HybridSearchService(
    embedding_service=_embedding_service,
    vector_store=_vector_store,
    bm25_retriever=_bm25_retriever,
    reranker=_reranker,
)

# Gán _search_service sang HybridSearchService để khi upload nạp cả BM25 và Vector
_search_service: Any = _hybrid_search_service

# 4. Khởi tạo LLM Provider, Gatekeeper, QueryRewriter & FaithfulnessVerifier
_context_builder = ContextBuilder(max_context_tokens=2000)
_llm_provider: BaseLLMProvider
if settings.gemini_api_key:
    _llm_provider = GeminiProvider(api_key=settings.gemini_api_key)
else:
    _llm_provider = MockLLMProvider()

_gatekeeper = RAGGatekeeper(
    accept_threshold=settings.gatekeeper_accept_threshold,
    reject_threshold=settings.gatekeeper_reject_threshold,
)
_query_rewriter = QueryRewriter(llm_provider=_llm_provider)
_faithfulness_verifier = FaithfulnessVerifier()

_rag_service = RAGService(
    retrieval_service=_hybrid_search_service,
    context_builder=_context_builder,
    llm_provider=_llm_provider,
    gatekeeper=_gatekeeper,
    query_rewriter=_query_rewriter,
    faithfulness_verifier=_faithfulness_verifier,
    enable_gatekeeper=settings.enable_gatekeeper,
    enable_verifier=settings.enable_faithfulness_verifier,
)

# Lưu trữ cache các tài liệu đã upload trong bộ nhớ
_documents_store: dict[str, ParsedDocument] = {}


def get_vector_store() -> BaseVectorStore:
    """Dependency cung cấp Vector Store."""
    return _vector_store


def get_embedding_service() -> EmbeddingService:
    """Dependency cung cấp Embedding Service."""
    return _embedding_service


def get_search_service() -> Any:
    """Dependency cung cấp Search Service."""
    return _search_service


def get_hybrid_search_service() -> HybridSearchService:
    """Dependency cung cấp Hybrid Search Service."""
    return _hybrid_search_service


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


def get_job_repo(db: Annotated[Session, Depends(get_db)]) -> JobRepository:
    return JobRepository(db)
