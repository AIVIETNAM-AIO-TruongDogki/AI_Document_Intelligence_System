import google.generativeai as genai

from app.llm.base import BaseLLMProvider, LLMRequest, LLMResponse


class GeminiProvider(BaseLLMProvider):
    """Provider giao tiếp với Google Gemini API thông qua Google Generative AI SDK."""

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash") -> None:
        if not api_key:
            raise ValueError("GEMINI_API_KEY không được để trống.")
        self.api_key = api_key
        self.model_name = model_name
        genai.configure(api_key=self.api_key)

    def generate(self, request: LLMRequest) -> LLMResponse:
        # Khởi tạo model kèm system_instruction (nếu có)
        model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=request.system_instruction,
        )

        generation_config = genai.types.GenerationConfig(
            temperature=request.temperature,
            max_output_tokens=request.max_tokens,
        )

        response = model.generate_content(
            contents=request.prompt,
            generation_config=generation_config,
        )

        # Lấy số lượng token từ usage_metadata nếu có
        prompt_tokens = 0
        completion_tokens = 0
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            prompt_tokens = getattr(response.usage_metadata, "prompt_token_count", 0) or 0
            completion_tokens = (
                getattr(response.usage_metadata, "candidates_token_count", 0) or 0
            )

        return LLMResponse(
            content=response.text if response.text else "",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

    def health_check(self) -> bool:
        """Kiểm tra API Key và model có hoạt động hay không."""
        try:
            # Gửi một ping đơn giản kiểm tra tính sẵn sàng của model
            model = genai.GenerativeModel(self.model_name)
            resp = model.generate_content("ping", generation_config={"max_output_tokens": 5})
            return bool(resp and resp.text)
        except Exception:  # noqa: BLE001
            return False
