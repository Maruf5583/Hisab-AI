import os
from typing import List, Optional
from app.core.config import settings
from app.document_processing.providers.base import (
    OCRProvider,
    OCRResult,
    OCRTextBlock,
    OCRConfigurationError,
    OCRError,
)


class GoogleVisionOCRProvider(OCRProvider):
    """Google Cloud Vision OCR adapter.
    
    Adheres strictly to the requirement that missing credentials must produce
    a clear, helpful error status instead of crashing application startup.
    """

    def __init__(self):
        self._client = None
        self._is_available = False
        self._init_error = None
        self._initialize()

    @property
    def provider_name(self) -> str:
        return "google_vision"

    def _initialize(self):
        # 1. Check if google-cloud-vision is installed
        try:
            from google.cloud import vision
            self._vision_module = vision
        except ImportError:
            self._init_error = "The 'google-cloud-vision' package is not installed. Install with 'pip install google-cloud-vision'."
            return

        # 2. Check credentials configuration
        creds_path = settings.GOOGLE_APPLICATION_CREDENTIALS or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if not creds_path:
            self._init_error = "GOOGLE_APPLICATION_CREDENTIALS is not configured in .env or environment variables."
            return

        if not os.path.exists(creds_path):
            self._init_error = f"Google Cloud credentials file not found at '{creds_path}'."
            return

        try:
            self._client = self._vision_module.ImageAnnotatorClient()
            self._is_available = True
        except Exception as e:
            self._init_error = f"Failed to initialize Google Vision client: {str(e)}"

    def is_configured(self) -> bool:
        return self._is_available

    def get_status_message(self) -> str:
        if self._is_available:
            return "Google Cloud Vision OCR is configured and operational."
        return self._init_error or "Google Cloud Vision OCR is not configured."

    def extract_text_from_image(self, image_bytes: bytes) -> OCRResult:
        if not self._is_available:
            raise OCRConfigurationError(
                f"Google Cloud Vision OCR is unavailable: {self._init_error}. "
                "Configure GOOGLE_APPLICATION_CREDENTIALS or switch OCR_PROVIDER=mock in .env for local development."
            )

        try:
            image = self._vision_module.Image(content=image_bytes)
            response = self._client.document_text_detection(image=image)

            if response.error.message:
                raise OCRError(f"Google Cloud Vision API error: {response.error.message}")

            full_text = response.full_text_annotation.text if response.full_text_annotation else ""
            blocks: List[OCRTextBlock] = []
            confidences = []

            if response.full_text_annotation and response.full_text_annotation.pages:
                for page in response.full_text_annotation.pages:
                    for block in page.blocks:
                        conf = block.confidence if hasattr(block, "confidence") and block.confidence else 1.0
                        confidences.append(conf)

                        # Bounding box from vertices
                        if block.bounding_box and block.bounding_box.vertices:
                            xs = [v.x for v in block.bounding_box.vertices if hasattr(v, "x")]
                            ys = [v.y for v in block.bounding_box.vertices if hasattr(v, "y")]
                            x0 = min(xs) if xs else 0.0
                            y0 = min(ys) if ys else 0.0
                            x1 = max(xs) if xs else 0.0
                            y1 = max(ys) if ys else 0.0
                        else:
                            x0, y0, x1, y1 = 0.0, 0.0, 0.0, 0.0

                        block_words = []
                        for paragraph in block.paragraphs:
                            for word in paragraph.words:
                                word_text = "".join(symbol.text for symbol in word.symbols)
                                block_words.append(word_text)

                        blocks.append(
                            OCRTextBlock(
                                text=" ".join(block_words),
                                bounding_box=(float(x0), float(y0), float(x1), float(y1)),
                                confidence=float(conf),
                            )
                        )

            avg_conf = sum(confidences) / len(confidences) if confidences else 1.0
            return OCRResult(
                full_text=full_text,
                blocks=blocks,
                confidence=round(avg_conf, 4),
                provider_name=self.provider_name,
            )
        except OCRConfigurationError:
            raise
        except Exception as e:
            raise OCRError(f"Google Cloud Vision OCR processing failed: {str(e)}")

    def extract_text_from_pdf_page(self, pdf_page_bytes: bytes) -> OCRResult:
        return self.extract_text_from_image(pdf_page_bytes)
