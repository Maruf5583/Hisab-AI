from typing import List, Tuple
from app.document_processing.providers.base import OCRProvider, OCRResult, OCRTextBlock


class MockOCRProvider(OCRProvider):
    """Deterministic OCR provider for local development, testing, and offline environments."""

    @property
    def provider_name(self) -> str:
        return "mock"

    def extract_text_from_image(self, image_bytes: bytes) -> OCRResult:
        # Generate clean synthetic Bengali/English text lines with bounding boxes
        blocks = [
            OCRTextBlock(
                text="মেসার্স রহিম ট্রেডার্স",
                bounding_box=(40.0, 50.0, 250.0, 80.0),
                confidence=0.98,
            ),
            OCRTextBlock(
                text="চালান নং: INV-2026-99",
                bounding_box=(40.0, 90.0, 200.0, 115.0),
                confidence=0.96,
            ),
            OCRTextBlock(
                text="তারিখ: ২৮/১০/২০২৬",
                bounding_box=(350.0, 90.0, 500.0, 115.0),
                confidence=0.95,
            ),
            OCRTextBlock(
                text="মোট টাকা: ১৫,৫০০.০০",
                bounding_box=(300.0, 400.0, 500.0, 430.0),
                confidence=0.97,
            ),
            OCRTextBlock(
                text="নগদ পরিশোধ: ৫,৫০০.০০",
                bounding_box=(300.0, 440.0, 500.0, 465.0),
                confidence=0.95,
            ),
            OCRTextBlock(
                text="বাকি টাকা: ১০,০০০.০০",
                bounding_box=(300.0, 475.0, 500.0, 500.0),
                confidence=0.94,
            ),
        ]

        full_text = "\n".join(b.text for b in blocks)
        return OCRResult(
            full_text=full_text,
            blocks=blocks,
            confidence=0.96,
            provider_name=self.provider_name,
            metadata={"mock": True, "size_bytes": len(image_bytes)},
        )

    def extract_text_from_pdf_page(self, pdf_page_bytes: bytes) -> OCRResult:
        return self.extract_text_from_image(pdf_page_bytes)
