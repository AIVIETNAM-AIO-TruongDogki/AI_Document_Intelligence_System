import pytest

from app.documents.models import Chunk
from app.embeddings.mock import MockEmbeddingProvider
from app.embeddings.service import EmbeddingService


def test_mock_embedding_provider_dimension_and_determinism() -> None:
    provider = MockEmbeddingProvider(dimension=64)
    assert provider.dimension == 64

    # Tính tất định: cùng 1 câu -> vector giống hệt nhau
    v1 = provider.embed_query("Trí tuệ nhân tạo")
    v2 = provider.embed_query("Trí tuệ nhân tạo")
    assert len(v1) == 64
    assert v1 == v2

    # Khác câu -> vector khác nhau
    v3 = provider.embed_query("Khoa học máy tính")
    assert v1 != v3


def test_mock_embedding_provider_invalid_dimension() -> None:
    with pytest.raises(ValueError, match="lớn hơn 0"):
        MockEmbeddingProvider(dimension=0)


def test_embedding_service_embed_chunks_and_query() -> None:
    provider = MockEmbeddingProvider(dimension=32)
    service = EmbeddingService(provider)

    chunks = (
        Chunk(
            chunk_id="c1",
            document_id="doc1",
            text="Hợp đồng mua bán",
            page_numbers=(1,),
            token_count=5,
        ),
        Chunk(
            chunk_id="c2",
            document_id="doc1",
            text="Điều khoản thanh toán",
            page_numbers=(2,),
            token_count=5,
        ),
    )

    returned_chunks, vectors = service.embed_chunks(chunks)
    assert len(returned_chunks) == 2
    assert len(vectors) == 2
    assert len(vectors[0]) == 32

    # Query rỗng phải văng lỗi ValueError
    with pytest.raises(ValueError, match="không được để trống"):
        service.embed_query("   ")
