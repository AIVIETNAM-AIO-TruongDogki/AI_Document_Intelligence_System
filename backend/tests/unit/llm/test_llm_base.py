from app.llm.base import LLMRequest, MockLLMProvider


def test_mock_llm_provider_default() -> None:
    provider = MockLLMProvider()
    assert provider.health_check() is True

    req = LLMRequest(prompt="Xin chào, bạn là ai?", temperature=0.0)
    resp = provider.generate(req)

    assert "Mock answer for prompt:" in resp.content
    assert resp.prompt_tokens > 0
    assert resp.completion_tokens > 0


def test_mock_llm_provider_fixed_answer() -> None:
    provider = MockLLMProvider(fixed_answer="Câu trả lời cố định.")
    req = LLMRequest(prompt="Bất kỳ câu hỏi nào")
    resp = provider.generate(req)

    assert resp.content == "Câu trả lời cố định."
    assert resp.completion_tokens == 5
