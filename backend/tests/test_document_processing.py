import io
import uuid
import pytest
import pymupdf
from PIL import Image
from fastapi.testclient import TestClient
from app.main import app
from app.document_processing.pdf_text import extract_pdf_native_text
from app.document_processing.providers.mock_provider import MockOCRProvider
from app.document_processing.providers.google_vision import GoogleVisionOCRProvider
from app.document_processing.providers.base import OCRConfigurationError

client = TestClient(app)


def setup_user_and_business(suffix: str):
    email = f"ocr_user_{suffix}@example.com"
    client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!", "full_name": f"User {suffix}"})
    token = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    biz_res = client.post(
        "/api/v1/businesses/",
        json={"name": f"OCR Biz {suffix}", "slug": f"ocr-biz-{suffix}", "currency": "BDT"},
        headers=headers,
    )
    biz_id = biz_res.json()["id"]
    headers["X-Business-Id"] = biz_id
    return headers, biz_id


def create_native_pdf(text: str = "চালান নং INV-9001\nমেসার্স আল-আমিন ট্রেডার্স\nমোট: ২৫,০০০.০০") -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((50, 80), text, fontsize=12)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def create_scanned_image() -> bytes:
    img = Image.new("RGB", (400, 300), color=(250, 250, 250))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_pdf_native_text_extraction():
    """Verify PyMuPDF extracts embedded text directly without OCR."""
    pdf_bytes = create_native_pdf("Invoice No: INV-123456\nCustomer: Rahim Brothers\nAmount: 50,000.00")
    res = extract_pdf_native_text(pdf_bytes)
    assert res.has_native_text is True
    assert res.total_pages == 1
    assert "INV-123456" in res.pages[0].raw_text
    assert "Rahim Brothers" in res.pages[0].raw_text
    assert len(res.pages[0].blocks) > 0


def test_process_native_pdf_pipeline():
    """End-to-end test: upload native PDF -> trigger process -> inspect extracted pages."""
    suffix = uuid.uuid4().hex[:8]
    headers, _ = setup_user_and_business(suffix)

    pdf_bytes = create_native_pdf("বিক্রয় চালান\nচালান নং: INV-5544\nমোট টাকা: ৩৫,০০০.০০")
    upload_res = client.post(
        "/api/v1/documents/upload",
        files={"file": ("invoice.pdf", pdf_bytes, "application/pdf")},
        headers=headers,
    )
    doc_id = upload_res.json()["id"]

    # Trigger process
    proc_res = client.post(f"/api/v1/documents/{doc_id}/process", headers=headers)
    assert proc_res.status_code == 200
    assert proc_res.json()["status"] == "needs_review"

    # Inspect extracted pages
    pages_res = client.get(f"/api/v1/documents/{doc_id}/pages", headers=headers)
    assert pages_res.status_code == 200
    pages = pages_res.json()
    assert len(pages) == 1
    assert pages[0]["has_native_text"] is True
    assert "INV-5544" in pages[0]["raw_text"]
    assert pages[0]["ocr_data"]["provider"] == "native_pdf"


def test_process_scanned_image_via_ocr():
    """End-to-end test: upload image -> trigger OCR processing -> verify blocks and confidence."""
    suffix = uuid.uuid4().hex[:8]
    headers, _ = setup_user_and_business(suffix)

    img_bytes = create_scanned_image()
    upload_res = client.post(
        "/api/v1/documents/upload",
        files={"file": ("receipt.png", img_bytes, "image/png")},
        headers=headers,
    )
    doc_id = upload_res.json()["id"]

    # Trigger OCR
    proc_res = client.post(f"/api/v1/documents/{doc_id}/process", headers=headers)
    assert proc_res.status_code == 200
    assert proc_res.json()["status"] == "needs_review"

    # Inspect OCR pages
    pages_res = client.get(f"/api/v1/documents/{doc_id}/pages", headers=headers)
    assert pages_res.status_code == 200
    pages = pages_res.json()
    assert len(pages) == 1
    assert pages[0]["has_native_text"] is False
    assert pages[0]["ocr_data"]["provider"] == "mock"
    assert pages[0]["ocr_data"]["confidence"] >= 0.9
    assert len(pages[0]["ocr_data"]["blocks"]) > 0
    assert "মেসার্স রহিম ট্রেডার্স" in pages[0]["raw_text"]


def test_google_vision_provider_missing_credentials_safety():
    """Verify Google Cloud Vision adapter does NOT crash application when credentials are not configured."""
    provider = GoogleVisionOCRProvider()
    assert provider.provider_name == "google_vision"
    # When credentials are not provided in environment, is_configured() is False
    assert provider.is_configured() is False
    assert "not configured" in provider.get_status_message().lower() or "not installed" in provider.get_status_message().lower()

    # Calling extraction without credentials raises clear OCRConfigurationError
    with pytest.raises(OCRConfigurationError) as exc_info:
        provider.extract_text_from_image(b"fake-image-bytes")
    assert "unavailable" in str(exc_info.value).lower()
