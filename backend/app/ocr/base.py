from abc import ABC, abstractmethod

class BaseOCRProvider(ABC):
    @abstractmethod
    def extract_text_from_image(self, image_bytes: bytes) -> str:
        """Nhận diện văn bản từ byte ảnh PNG/JPEG."""
        ...