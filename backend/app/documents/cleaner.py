import re
import unicodedata


def clean_text(text: str) -> str:
    if not text:
        return ""

    # 1. Chuẩn hóa NFKC để tách ligature (VD: 'ﬁ' -> 'fi') và NFC cho tiếng Việt
    text = unicodedata.normalize("NFKC", text)
    text = unicodedata.normalize("NFC", text)

    # 2. Chuẩn hóa ký tự ngắt dòng: \r\n (Windows) và \r (Mac cũ) về \n (Unix)
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 3. Lọc bỏ các ký tự điều khiển rác (Control Characters), giữ lại \n và \t
    text = "".join(
        char for char in text
        if char in "\n\t" or unicodedata.category(char) != "Cc"
    )

    # 4. Gom nhiều khoảng trắng ngang liên tiếp thành 1 dấu cách duy nhất
    text = re.sub(r"[ \t]+", " ", text)

    # 5. Gom từ 3 dấu xuống dòng trở lên thành 2 dấu xuống dòng (ngắt đoạn chuẩn)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()