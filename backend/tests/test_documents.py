import io
import uuid
import pytest
import pymupdf
from PIL import Image
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def setup_user_and_business(suffix: str):
    email = f"doc_user_{suffix}@example.com"
    client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!", "full_name": f"User {suffix}"})
    token = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    biz_res = client.post(
        "/api/v1/businesses/",
        json={"name": f"Doc Test Business {suffix}", "slug": f"doc-biz-{suffix}", "currency": "BDT"},
        headers=headers,
    )
    biz_id = biz_res.json()["id"]
    headers["X-Business-Id"] = biz_id
    return headers, biz_id


def create_synthetic_pdf(text: str = "চালান নং ১২৩৪৫\nমেসার্স সততা এন্টারপ্রাইজ") -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((50, 72), text, fontsize=12)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def create_synthetic_image() -> bytes:
    img = Image.new("RGB", (300, 200), color=(240, 240, 240))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_pdf_upload_download_and_duplicate_detection():
    suffix = uuid.uuid4().hex[:8]
    headers, _ = setup_user_and_business(suffix)

    pdf_bytes = create_synthetic_pdf(" চালান নং INV-1001 \n মোট টাকা: 15,000 ")

    # 1. Upload valid PDF
    files = {"file": ("test_invoice.pdf", pdf_bytes, "application/pdf")}
    data = {"document_type": "sales_invoice"}
    res = client.post("/api/v1/documents/upload", files=files, data=data, headers=headers)
    assert res.status_code == 201, res.text
    doc = res.json()
    doc_id = doc["id"]
    assert doc["original_filename"] == "test_invoice.pdf"
    assert doc["page_count"] == 1
    assert doc["document_type"] == "sales_invoice"
    assert doc["status"] == "uploaded"
    assert len(doc["file_hash_sha256"]) == 64

    # 2. Reject duplicate identical upload
    dup_res = client.post(
        "/api/v1/documents/upload",
        files={"file": ("duplicate_file.pdf", pdf_bytes, "application/pdf")},
        data=data,
        headers=headers,
    )
    assert dup_res.status_code == 409
    assert "Duplicate document" in dup_res.json()["detail"]

    # 3. Authorized download
    dl_res = client.get(f"/api/v1/documents/{doc_id}/download", headers=headers)
    assert dl_res.status_code == 200
    assert dl_res.content == pdf_bytes
    assert "application/pdf" in dl_res.headers.get("content-type", "")

    # 4. Reject document
    rej_res = client.post(
        f"/api/v1/documents/{doc_id}/reject",
        json={"reason": "কাগজের ছবি অস্পষ্ট, পুনরায় আপলোড করুন"},
        headers=headers,
    )
    assert rej_res.status_code == 200
    assert rej_res.json()["status"] == "rejected"
    assert rej_res.json()["rejection_reason"] == "কাগজের ছবি অস্পষ্ট, পুনরায় আপলোড করুন"


def test_image_upload_and_invalid_extensions():
    suffix = uuid.uuid4().hex[:8]
    headers, _ = setup_user_and_business(suffix)

    # 1. Upload valid PNG image
    png_bytes = create_synthetic_image()
    files = {"file": ("receipt.png", png_bytes, "image/png")}
    res = client.post("/api/v1/documents/upload", files=files, headers=headers)
    assert res.status_code == 201
    assert res.json()["page_count"] == 1

    # 2. Reject disallowed file extension (.exe)
    bad_files = {"file": ("malicious.exe", b"not-a-real-exe", "application/x-msdownload")}
    bad_res = client.post("/api/v1/documents/upload", files=bad_files, headers=headers)
    assert bad_res.status_code == 400
    assert "not supported" in bad_res.json()["detail"]


def test_document_cross_tenant_isolation():
    """Verify that documents cannot be downloaded or viewed across workspaces."""
    s1 = uuid.uuid4().hex[:8]
    s2 = uuid.uuid4().hex[:8]
    headers_1, _ = setup_user_and_business(s1)
    headers_2, _ = setup_user_and_business(s2)

    # Upload document to Business 1
    pdf_bytes = create_synthetic_pdf("Private document for Business 1")
    res1 = client.post(
        "/api/v1/documents/upload",
        files={"file": ("biz1_invoice.pdf", pdf_bytes, "application/pdf")},
        headers=headers_1,
    )
    doc_1_id = res1.json()["id"]

    # 1. User 2 cannot GET Business 1's document metadata
    cross_get = client.get(f"/api/v1/documents/{doc_1_id}", headers=headers_2)
    assert cross_get.status_code == 404

    # 2. User 2 cannot download Business 1's document file
    cross_dl = client.get(f"/api/v1/documents/{doc_1_id}/download", headers=headers_2)
    assert cross_dl.status_code == 404

    # 3. User 2 cannot reject Business 1's document
    cross_rej = client.post(
        f"/api/v1/documents/{doc_1_id}/reject",
        json={"reason": "Attempted unauthorized reject"},
        headers=headers_2,
    )
    assert cross_rej.status_code == 404

    # 4. Business 2 inbox does NOT contain Business 1's document
    inbox_res = client.get("/api/v1/documents/", headers=headers_2)
    doc_ids = [d["id"] for d in inbox_res.json()["items"]]
    assert doc_1_id not in doc_ids
