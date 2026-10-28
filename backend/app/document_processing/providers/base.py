from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any, Optional


@dataclass
class OCRTextBlock:
    text: str
    bounding_box: Tuple[float, float, float, float]  # (x0, y0, x1, y1)
    confidence: float = 1.0


@dataclass
class OCRResult:
    full_text: str
    blocks: List[OCRTextBlock] = field(default_factory=list)
    confidence: float = 1.0
    provider_name: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)


class OCRError(Exception):
    """Base exception for OCR provider errors."""
    pass


class OCRConfigurationError(OCRError):
    """Raised when an OCR provider is requested but its configuration or credentials are missing."""
    pass


class OCRProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the OCR provider."""
        pass

    @abstractmethod
    def extract_text_from_image(self, image_bytes: bytes) -> OCRResult:
        """Extract text and bounding blocks from raw image bytes."""
        pass

    @abstractmethod
    def extract_text_from_pdf_page(self, pdf_page_bytes: bytes) -> OCRResult:
        """Extract text and bounding blocks from a rendered PDF page image."""
        pass
