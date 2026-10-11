RAG_SYSTEM_INSTRUCTION = """Bạn là trợ lý hỏi đáp tài liệu DocMind. 
Nhiệm vụ của bạn là trả lời câu hỏi của người dùng CHỈ dựa trên các tài liệu được cung cấp trong phần <context>.

Quy tắc bắt buộc:
1. Chỉ sử dụng thông tin có trong <context>. Tuyệt đối không suy đoán hoặc sử dụng kiến thức bên ngoài.
2. Nếu ngữ cảnh không chứa đủ thông tin để trả lời, hãy trả lời chính xác: "Thông tin này không được đề cập trong tài liệu được cung cấp."
3. Gắn trích dẫn nguồn vào cuối các ý trả lời theo định dạng [Nguồn X], trong đó X là số thứ tự tài liệu trong context.
"""


def format_rag_prompt(query: str, context_text: str) -> str:
    """Ráp câu hỏi của người dùng và văn bản ngữ cảnh vào prompt chuẩn."""
    return f"""<context>
{context_text}
</context>

Câu hỏi: {query}
Câu trả lời:"""