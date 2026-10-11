from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class LLMRequest:
    """Yêu cầu gửi tới LLM Engine."""

    prompt: str
    system_instruction: str | None = None
    temperature: float = 0.0
    max_tokens: int | None = 1024


@dataclass(frozen=True)
class LLMResponse:
    """Kết quả phản hồi từ LLM Engine."""

    content: str
    prompt_tokens: int = 0
    completion_tokens: int = 0


class BaseLLMProvider(ABC):
    """Giao diện trừu tượng tuân thủ Dependency Inversion cho mọi LLM engine."""

    @abstractmethod
    def generate(self, request: LLMRequest) -> LLMResponse:
        """Sinh câu trả lời đồng bộ."""

    @abstractmethod
    def health_check(self) -> bool:
        """Kiểm tra kết nối và tính sẵn sàng của LLM API."""


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM trả lời tất định cho mục đích Unit Test và kiểm thử offline."""

    def __init__(self, fixed_answer: str | None = None) -> None:
        self.fixed_answer = fixed_answer

    def generate(self, request: LLMRequest) -> LLMResponse:
        prompt_tokens = len(request.prompt.split()) if request.prompt else 0

        if self.fixed_answer is not None:
            content = self.fixed_answer
        else:
            content = (
                f"Mock answer for prompt: {request.prompt[:60]}..."
                if request.prompt
                else "Mock answer"
            )

        completion_tokens = len(content.split())
        return LLMResponse(
            content=content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

    def health_check(self) -> bool:
        return True