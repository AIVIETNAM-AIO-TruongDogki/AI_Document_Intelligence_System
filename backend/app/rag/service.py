from dataclasses import dataclass

from app.llm.base import BaseLLMProvider, LLMRequest
from app.rag.context_builder import CitationSource, ContextBuilder
from app.rag.prompt import RAG_SYSTEM_INSTRUCTION, format_rag_prompt
from app.retrieval.service import HybridSearchService


@dataclass(frozen=True)
class RAGAnswer:
    answer: str
    sources: list[CitationSource]
    model_name: str
    tokens_used: dict[str, int]


class RAGService:
    """Service điều phối toàn diện cho quy trình RAG (Retrieval-Augmented Generation)."""

    def __init__(
        self,
        retrieval_service: HybridSearchService,
        context_builder: ContextBuilder,
        llm_provider: BaseLLMProvider,
    ) -> None:
        self.retrieval_service = retrieval_service
        self.context_builder = context_builder
        self.llm_provider = llm_provider

    def answer_question(
        self,
        query: str,
        document_id: str | None = None,
        top_k: int = 5,
    ) -> RAGAnswer:
        """Thực thi pipeline RAG từ đầu đến cuối và trả về câu trả lời kèm bằng chứng."""
        cleaned_query = query.strip()
        if not cleaned_query:
            raise ValueError("Câu hỏi không được để trống.")

        # Truy hồi các đoạn trích liên quan nhất qua Hybrid Search
        search_results = self.retrieval_service.search(
            query=cleaned_query,
            top_k=top_k,
            document_id=document_id,
        )

        # Xây dựng khối ngữ cảnh và danh sách nguồn theo ngân sách token
        built_context = self.context_builder.build(search_results)

        # Ráp ngữ cảnh và câu hỏi vào khung prompt chuẩn chống ảo giác
        rag_prompt = format_rag_prompt(
            query=cleaned_query,
            context_text=built_context.context_text,
        )

        # Gửi yêu cầu tới LLM Engine
        llm_request = LLMRequest(
            prompt=rag_prompt,
            system_instruction=RAG_SYSTEM_INSTRUCTION,
            temperature=0.0,
            max_tokens=1024,
        )
        llm_response = self.llm_provider.generate(llm_request)

        # Xác định model_name và đóng gói kết quả
        model_name = getattr(self.llm_provider, "model_name", self.llm_provider.__class__.__name__)
        tokens_used = {
            "prompt_tokens": llm_response.prompt_tokens,
            "completion_tokens": llm_response.completion_tokens,
            "total_tokens": llm_response.prompt_tokens + llm_response.completion_tokens,
        }

        return RAGAnswer(
            answer=llm_response.content,
            sources=built_context.sources,
            model_name=model_name,
            tokens_used=tokens_used,
        )
