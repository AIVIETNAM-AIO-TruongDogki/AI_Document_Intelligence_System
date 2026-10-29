import hashlib
from pathlib import Path

class OCRCache:
    """Cache kết quả OCR trên ổ đĩa dựa trên SHA-256 của ảnh."""
    def __init__(self, cache_dir: str = ".cache/ocr") -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _hash(self, image_bytes: bytes) -> str:
        return hashlib.sha256(image_bytes).hexdigest()

    def get(self, image_bytes: bytes) -> str | None:
        file_path = self.cache_dir / f"{self._hash(image_bytes)}.txt"
        if file_path.is_file():
            return file_path.read_text(encoding="utf-8")
        return None

    def set(self, image_bytes: bytes, text: str) -> None:
        file_path = self.cache_dir / f"{self._hash(image_bytes)}.txt"
        file_path.write_text(text, encoding="utf-8")