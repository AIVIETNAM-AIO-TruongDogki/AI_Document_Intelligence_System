from app.documents.cleaner import clean_text


def test_clean_text_normalizes_vietnamese_nfc_and_whitespace() -> None:
    # 'Hoà' dùng dấu tổ hợp NFD và nhiều khoảng trắng thừa
    raw_input = "Xin   chào\r\n\r\n\r\nĐại học   Bách Khoa\t\tHà Nội"
    expected = "Xin chào\n\nĐại học Bách Khoa Hà Nội"
    assert clean_text(raw_input) == expected


def test_clean_text_preserves_math_and_punctuation() -> None:
    raw_input = "  Phương trình: f(x) = x^2 + 2x + 1 >= 0; [x in R].  "
    expected = "Phương trình: f(x) = x^2 + 2x + 1 >= 0; [x in R]."
    assert clean_text(raw_input) == expected