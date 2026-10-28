from app.core.config import settings
from app.document_processing.providers.base import OCRProvider
from app.document_processing.providers.mock_provider import MockOCRProvider
from app.document_processing.providers.google_vision import GoogleVisionOCRProvider


def get_ocr_provider(provider_name: str | None = None) -> OCRProvider:
    """Return the configured OCR provider instance."""
    name = (provider_name or settings.OCR_PROVIDER or "mock").strip().lower()

    if name == "google_vision":
        return GoogleVisionOCRProvider()
    elif name == "mock":
        return MockOCRProvider()
    else:
        # Fallback to mock provider with a warning
        return MockOCRProvider()
